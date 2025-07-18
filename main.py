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
    summary = "Sorry, we could not process your request. Please try again or contact support if the issue persists."  # Default summary for failure
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
            f"You are an expert Python developer with full CRUD permissions on the file at '{modified_path}'.\n"
            f"The user’s goal: {task!r}\n\n"
            "STEP 1 – INSPECTION:\n"
            "- Open and read every sheet in the file at the given path ('{modified_path}').\n"
            "- Identify its schema: sheet names, headers, data types, formulas, and any metadata.\n\n"
            "STEP 2 – PLANNING:\n"
            "- Produce a clear, ordered plan of exactly what to change (e.g. sheet 'Sales', row 4 column 'Amount', update formula X→Y).\n"
            "- Reference specific sheets, rows, columns and explain why each change is needed for the user’s goal.\n\n"
            "STEP 3 – CODE GENERATION:\n"
            "- Translate your plan into pure Python code (no markdown or fenced blocks) that:\n"
            "    • Accepts the file path ('{modified_path}') as input\n"
            "    • Uses only pip‑installable libraries (e.g. pandas, openpyxl, python‑libreoffice)\n"
            "    • Does NOT use Microsoft Office tools—use only LibreOffice-compatible tools\n"
            "    • Does NOT use packages that do not exist on PyPI\n"
            "    • Modifies the file in place\n"
            "- At the end of your script, print a single line starting with 'SUMMARY:' listing each change performed (e.g. 'SUMMARY: Sheet \"Data\", row 4 col \"Name\" changed to \"Alice\"').\n\n"
            "Ensure your code logically follows your plan, leverages all relevant information in the file, and uses only pip‑installable packages."
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
            summary = ""
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
                f"The code you generated to process '{modified_path}' failed with this error:\n{e.stderr}\n\n"
                "Please revisit your PLAN and correct only the specific code sections that caused this error.\n"
                "- Do NOT rewrite the entire script—show only the changed lines or blocks.\n"
                "- Maintain the same input signature (file path) and output format (print 'SUMMARY:' at end).\n"
                "- Continue using only pip‑installable Python packages and LibreOffice-compatible tools.\n"
                "- Do NOT include any markdown, code block, or ```python formatting.\n\n"
                "Output only the corrected Python code."
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
            f"You are a meticulous validator. The user requested: {task!r}.\n"
            "You have two files:\n"
            f"  • Original: '{file_path}'\n"
            f"  • Modified: '{modified_path}'\n\n"
            "VALIDATION STEPS:\n"
            "1. Open and read both the original and modified Excel files at their respective paths.\n"
            "2. Compare the executor’s intended PLAN to the actual modifications in '{modified_path}'.\n"
            "3. Check for any unintended edits in data values, formulas, formatting, or metadata.\n"
            "4. Check for any mistakes or inconsistencies in the modified file."
            "5. Confirm every requested change is present, and no other cells were altered.\n\n"
            "If everything matches exactly, reply:\n"
            "  YES\n"
            "  Briefly list the validations you performed (e.g. 'Checked sheet X rows 1–5, columns A–D').\n\n"
            "If you find any discrepancy, reply:\n"
            "  NO\n"
            "  For each issue, specify:\n"
            "    - What was expected (based on user request)\n"
            "    - What you observed instead (sheet, row, col, old→new)\n\n"
            "This detail will guide the executor to correct its code. Do NOT include any extra text."
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
            "The validator identified the following issues:\n"
            f"{validation}\n\n"
            f"Original file path: '{file_path}'\n"
            f"Modified file path: '{modified_path}'\n\n"
            "Please adjust your code to resolve these specific discrepancies.\n"
            "- Do NOT rewrite unchanged sections—only output the corrected code segments.\n"
            "- Maintain the same input signature and print 'SUMMARY:' after applying your fixes.\n"
            "- Continue using only pip‑installable Python packages and LibreOffice-compatible tools.\n"
            "- Do NOT include any markdown, code block, or ```python formatting.\n\n"
            "Output only the revised Python code."
        )
        print("[GENERATOR] Validator feedback to Gemini:")
        print(feedback_prompt)
        code = call_gemini(feedback_prompt)
    print("[FAILURE] Could not process the request after several attempts.")
    message = "Sorry, the task could not be fully completed. Here is your file (may be unchanged or partially changed)."
    print(f"[FAILURE] {message}")
    headers = {"X-Task-Status": message, "X-Task-Summary": summary}
    return FileResponse(modified_path, filename=f"updated_{os.path.basename(file_path)}", headers=headers) 