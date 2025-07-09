import os
import shutil
import tempfile
import uuid
import subprocess
from fastapi import FastAPI, Form, Body
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
import requests
from pydantic import BaseModel

app = FastAPI()

# Set temp and codes directories outside the Agent365_2..0 folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
TEMP_DIR = os.path.join(PARENT_DIR, "temp")
CODES_DIR = os.path.join(PARENT_DIR, "codes")
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(CODES_DIR, exist_ok=True)

# Load environment variables from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 

def call_gemini(prompt, files=None):
    """
    Calls the Gemini API with the given prompt and optional files.
    Returns the response text.
    """
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}

    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    response = requests.post(url, headers=headers, params=params, json=data)
    if response.status_code != 200:
        raise Exception(f"Gemini API error: {response.status_code} {response.text}")
    result = response.json()
    # Extract the generated text
    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        raise Exception(f"Unexpected Gemini API response: {result}")


def install_dependencies(code):
    # Extract and install dependencies from code (very basic)
    import re
    pkgs = re.findall(r'import (\w+)', code) + re.findall(r'from (\w+) import', code)
    for pkg in set(pkgs):
        try:
            __import__(pkg)
        except ImportError:
            subprocess.run(["pip", "install", pkg])


class ProcessRequest(BaseModel):
    file_path: str
    task: str

@app.post("/process/")
async def process_file(request: ProcessRequest):
    file_path = request.file_path
    task = request.task
    print("Received file path and task:")
    print(f"  File path: {file_path}")
    print(f"  Task: {task}")
    # Make a copy of the original file to work on
    import uuid, os
    modified_path = os.path.join(TEMP_DIR, f"modified_{uuid.uuid4()}_{os.path.basename(file_path)}")
    shutil.copy2(file_path, modified_path)
    print(f"Copied original file to {modified_path}")

    # Agent loop
    for attempt in range(5):
        print(f"\n--- Attempt {attempt+1} ---")
        # 1. Generate steps and code
        prompt = (
            f"You are an expert Python developer. The user wants to: '{task}' "
            f"on the file at path: '{modified_path}'. "
            "You have full CRUD (Create, Read, Update, Delete) permissions on this file. "
            "You are allowed to read all details from the file to make any changes required by the user. "
            "Perform all operations directly in the Excel file, and ensure all changes are reflected in the file. "
            "At the end, output a detailed summary of what was changed and where (e.g., 'at row 4, changed name to ...'). "
            "Generate a step-by-step plan, then generate Python code to accomplish this. "
            "The code should take the file path as input and save the result in-place. "
            "Only output the code, nothing else. Do NOT include any markdown, code block, or ```python formatting.\n"
            "Only use pip-installable packages such as openpyxl, pandas, etc. "
            "Do not use packages that do not exist on PyPI."
        )
        print("[GENERATOR] Prompt to Gemini:")
        print(prompt)
        code = call_gemini(prompt)
        print("[GENERATOR] Code generated:")
        print(code)
        code_path = os.path.join(CODES_DIR, f"{uuid.uuid4()}_exec.py")
        with open(code_path, "w") as f:
            f.write(code)
        print(f"Saved generated code to {code_path}")

        # 2. Install dependencies
        try:
            print("[DEPENDENCIES] Installing dependencies (if needed)...")
            install_dependencies(code)
            print("[DEPENDENCIES] Dependency installation complete.")
        except Exception as e:
            print(f"[DEPENDENCIES] Dependency install failed: {e}")
            return JSONResponse({"error": f"Dependency install failed: {e}"}, status_code=500)

        # 3. Execute code
        try:
            print(f"[EXECUTION] Running generated code on {modified_path}...")
            result = subprocess.run(["python", code_path, modified_path], check=True, capture_output=True, text=True)
            print("[EXECUTION] Code execution stdout:")
            print(result.stdout)
            print("[EXECUTION] Code execution stderr:")
            print(result.stderr)
            # Extract summary from stdout
            summary = None
            for line in result.stdout.splitlines():
                if line.strip().lower().startswith("summary:"):
                    summary = line.strip()[len("summary:"):].strip()
            if not summary:
                summary = "No summary found in model output."
            print(f"[SUMMARY] {summary}")
        except subprocess.CalledProcessError as e:
            print(f"[EXECUTION] Error during code execution:")
            print(e.stderr)
            # Send error back to agent
            error_prompt = (
                f"The following error occurred while running your code:\n{e.stderr}\n"
                "Please fix the code and output only the corrected code. Do NOT include any markdown, code block, or ```python formatting."
            )
            print("[GENERATOR] Prompting Gemini for code correction:")
            print(error_prompt)
            code = call_gemini(error_prompt)
            continue

        # 4. Validate with second agent
        with open(file_path, "rb") as f:
            original_file_bytes = f.read()
        with open(modified_path, "rb") as f:
            modified_file_bytes = f.read()
        validate_prompt = (
            f"User asked: '{task}'. Here is the original file and the modified file. "
            "Check that ONLY the requested task has been executed and nothing else has been changed. "
            "If the task is completed and no other changes are present, reply 'YES' and explain. Otherwise, reply 'NO' and explain what is wrong."
        )
        print("[VALIDATOR] Prompt to Gemini:")
        print(validate_prompt)
        # Do NOT include the generated code in the validation prompt or files
        validation = call_gemini(validate_prompt, files={"original_file": original_file_bytes, "modified_file": modified_file_bytes})
        print("[VALIDATOR] Gemini response:")
        print(validation)
        if "YES" in validation.upper():
            print("[SUCCESS] Task validated successfully. Returning updated file.")
            headers = {"X-Task-Summary": summary}
            return FileResponse(modified_path, filename=f"updated_{os.path.basename(file_path)}", headers=headers)
        # else, feedback to executor agent
        feedback_prompt = (
            f"The validator says: {validation}\n"
            "Please fix your code and output only the corrected code. Do NOT include any markdown, code block, or ```python formatting."
        )
        print("[GENERATOR] Validator feedback to Gemini:")
        print(feedback_prompt)
        code = call_gemini(feedback_prompt)
    print("[FAILURE] Could not process the request after several attempts.")
    message = "Sorry, the task could not be fully completed. Here is your file (may be unchanged or partially changed)."
    print(f"[FAILURE] {message}")
    headers = {"X-Task-Status": message, "X-Task-Summary": summary}
    return FileResponse(modified_path, filename=f"updated_{os.path.basename(file_path)}", headers=headers) 