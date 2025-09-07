import os
import shutil
import uuid
import subprocess
from fastapi import APIRouter, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from utils.db_table import insert_office_agent_record
from ..HelperClass import call_gemini, install_dependencies, TEMP_DIR, CODES_DIR

router = APIRouter()
security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    # Global auth already validated in app dependencies; here we just read the username
    return credentials.username

class ProcessRequest(BaseModel):
    chat_name: str
    file_path: str
    task: str

@router.post("/process/")
async def process_file(request: ProcessRequest, current_user: str = Depends(get_current_username)):
    try:
        file_path = request.file_path
        task = request.task
        chat_name = request.chat_name
        summary = "Sorry, we could not process your request. Please try again or contact support if the issue persists."  # Default summary for failure
        print("Received file path and task:")
        print(f"  File path: {file_path}")
        print(f"  Task: {task}")
        # Make a copy of the original file to work on
        modified_path = os.path.join(TEMP_DIR, f"modified_{uuid.uuid4()}_{os.path.basename(file_path)}")
        shutil.copy2(file_path, modified_path)
        print(f"Copied original file to {modified_path}")

        # Agent loop
        for attempt in range(5):
            print(f"\n--- Attempt {attempt+1} ---")
            # 1. Generate steps and code
            prompt = (
                f"You are an expert Python developer with full CRUD permissions on the file at '{modified_path}'.\n"
                f"The user's goal: {task!r}\n\n"
                "Make sure to put all planning steps in the code in comments. And any extra text you add in the code as comments."
                "Leave notes for yourself in the code as comments."
                "When adding new things like images etc thinks properly and properly manage layout keeping the document presentable"
                "Only write python codes and make sure not to add anything like ```python or file name in the code"
                "STEP 1 – INSPECTION:\n"
                "- Open and read every sheet in the file at the given path ('{modified_path}').\n"
                "- Identify its schema: sheet names, headers, data types, formulas, and any metadata.\n\n"
                "STEP 2 – PLANNING:\n"
                "- Produce a clear, ordered plan of exactly what to change (e.g. sheet 'Sales', row 4 column 'Amount', update formula X→Y).\n"
                "- Reference specific sheets, rows, columns and explain why each change is needed for the user's goal.\n\n"
                "STEP 3 – CODE GENERATION:\n"
                "- Translate your plan into pure Python code (no markdown or fenced blocks) that:\n"
                "    • Accepts the file path ('{modified_path}') as input\n"
                "    • Does NOT use Microsoft Office tools—use only LibreOffice-compatible tools\n"
                "    • Does NOT use packages that do not exist on PyPI\n"
                "    • Modifies the file in place\n"
                "    • Before importing any external library, check if it is already installed and meets version requirements; only install via pip if missing or outdated.\n"
                "    • If you add a visual representation make sure to add legends, titles, class names, class labels, class values, scale, values on x and y axis and other relevant information to make it more presentable. If you have to add new columns for making charts show those columns in data (only if not already present) unless expliciptly told by user not to do so. \n"
                "    • Properly set and show the scale of the chart and set appropriate distance between labels for the axis if applicable. \n"
                "- At the end of your script, print a single line starting with 'SUMMARY:' listing each change performed (e.g. 'SUMMARY: Sheet \"Data\", row 4 col \"Name\" changed to \"Alice\"').\n\n"
                "Ensure your code logically follows your plan, leverages all relevant information in the file, and uses only pip-installable packages.\n\n"
                "For Word (.docx) documents:\n"
                "- STEP 1: Inspect all paragraphs, runs, tables, headers, and footers in the file at '{modified_path}'.\n"
                "- STEP 2: Plan edits by referencing exact paragraph indices, table cells, headers/footers, or styles to be changed.\n"
                "- STEP 3: Generate Python code (using python-docx) to implement these edits, ensuring correct formatting, spacing, and layout. If inserting images or charts, manage placement and scaling properly. Keep the document clean and readable.\n\n"
                "For PowerPoint (.pptx) presentations:\n"
                "- STEP 1: Inspect all slides, placeholders, shapes, text boxes, images, and charts in the file at '{modified_path}'.\n"
                "- STEP 2: Plan edits by referencing exact slide numbers and shape indices, describing why each change supports the user's goal.\n"
                "- STEP 3: Generate Python code (using python-pptx) to perform these edits. When adding images, shapes, or charts, ensure proper layout, alignment, labels, and legends. Titles and subtitles must remain clear and visually consistent. Charts must have correct axes, scales, and legends.\n\n"
            )
            print("[GENERATOR] Prompt to Gemini:")
            print(prompt)
            
            # Use streaming for large prompts to avoid token limit issues
            use_streaming = len(prompt) > 2000  # Use streaming for prompts longer than 2000 chars
            if use_streaming:
                print("[GENERATOR] Using streaming mode for large prompt...")
            
            try:
                code = call_gemini(prompt, stream=use_streaming)
            except Exception as e:
                error_text = str(e).lower()
                if use_streaming and ("empty-response" in error_text or "empty response" in error_text or "empty text" in error_text):
                    print("[GENERATOR] Streaming produced empty output, retrying in non-streaming mode...")
                    code = call_gemini(prompt, stream=False)
                else:
                    raise e
            print("[GENERATOR] Code generated:")
            print(code)
            code_path = os.path.join(CODES_DIR, f"{uuid.uuid4()}_exec.py")
            
            # Clean the code to handle encoding issues
            # Replace smart quotes and other problematic characters
            cleaned_code = code.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
            cleaned_code = cleaned_code.replace('–', '-').replace('—', '-').replace('…', '...')
            
            # Add UTF-8 encoding declaration at the top
            if not cleaned_code.startswith('# -*- coding: utf-8 -*-') and not cleaned_code.startswith('#coding: utf-8'):
                cleaned_code = '# -*- coding: utf-8 -*-\n' + cleaned_code
            
            with open(code_path, "w", encoding="utf-8") as f:
                f.write(cleaned_code)
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
                result = subprocess.run(
                    ["python", code_path, modified_path], 
                    check=True, 
                    capture_output=True, 
                    text=True,
                    encoding='utf-8',
                    errors='replace'  # Replace problematic characters instead of failing
                )
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
                code = call_gemini(error_prompt, stream=True)  # Use streaming for error corrections
                continue

            # 4. Validate with second agent
            try:
                with open(file_path, "rb") as f:
                    original_file_bytes = f.read()
                with open(modified_path, "rb") as f:
                    modified_file_bytes = f.read()
                validate_prompt = (
                    f"You are a meticulous validator. The user requested: {task!r}.\n"
                    "You have two files:\n"
                    f"  • Original: '{file_path}'\n"
                    f"  • Modified: '{modified_path}'\n\n"
                    "Leave notes for yourself in the code as comments."
                    "VALIDATION STEPS:\n"
                    "1. Open and read both the original and modified Excel files at their respective paths.\n"
                    "2. Compare the executor's intended PLAN to the actual modifications in '{modified_path}'.\n"
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
                validation = call_gemini(validate_prompt, files={"original_file": original_file_bytes, "modified_file": modified_file_bytes}, stream=True)
                print("[VALIDATOR] Gemini response:")
                print(validation)
                if "YES" in validation.upper():
                    print("[SUCCESS] Task validated successfully. Returning updated file.")
                    headers = {"X-Task-Summary": summary}
                    # Log success to DB before returning
                    try:
                        insert_office_agent_record(
                            user_id=(current_user or "")[:8],
                            chat_name=chat_name,
                            input_file_path=file_path,
                            output_file_path=modified_path,
                            query=task,
                            remarks=f"200 OK | {summary}"
                        )
                    except Exception as db_err:
                        print(f"[DB] Insert failed: {db_err}")
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
                code = call_gemini(feedback_prompt, stream=True)  # Use streaming for feedback
            except Exception as validation_error:
                print(f"[VALIDATION] Validation step failed: {validation_error}")
                print("[VALIDATION] Skipping validation and returning file as-is")
                # If validation fails, we'll still return the file but with a warning
                summary = f"{summary} (Note: Validation step failed due to: {str(validation_error)})"
                headers = {"X-Task-Summary": summary, "X-Validation-Status": "Failed"}
                # Log with warning to DB
                try:
                    insert_office_agent_record(
                        user_id=(current_user or "")[:8],
                        chat_name=chat_name,
                        input_file_path=file_path,
                        output_file_path=modified_path,
                        query=task,
                        remarks=f"200 OK (Validation failed) | {summary}"
                    )
                except Exception as db_err:
                    print(f"[DB] Insert failed: {db_err}")
                return FileResponse(modified_path, filename=f"updated_{os.path.basename(file_path)}", headers=headers)
        print("[FAILURE] Could not process the request after several attempts.")
        message = "Sorry, the task could not be fully completed. Here is your file (may be unchanged or partially changed)."
        print(f"[FAILURE] {message}")
        headers = {"X-Task-Status": message, "X-Task-Summary": summary}
        # Log failure to DB
        try:
            insert_office_agent_record(
                user_id=(current_user or "")[:8],
                chat_name=chat_name,
                input_file_path=file_path,
                output_file_path=modified_path,
                query=task,
                remarks=f"500 ERROR | {message} | {summary}"
            )
        except Exception as db_err:
            print(f"[DB] Insert failed: {db_err}")
        return FileResponse(modified_path, filename=f"updated_{os.path.basename(file_path)}", headers=headers)
    except Exception as e:
        print(f"[ERROR] Unexpected error in process_file: {e}")
        # Log unexpected error to DB
        try:
            insert_office_agent_record(
                user_id=str(uuid.uuid4())[:8],
                chat_name=request.chat_name if hasattr(request, 'chat_name') else "",
                input_file_path=request.file_path if hasattr(request, 'file_path') else "",
                output_file_path="",
                query=request.task if hasattr(request, 'task') else "",
                remarks=f"500 ERROR | {str(e)}"
            )
        except Exception as db_err:
            print(f"[DB] Insert failed: {db_err}")
        return JSONResponse(
            {"error": f"Internal server error: {str(e)}"}, 
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
