"""
executor.py - Core file processing and execution logic for Agent365
"""

import os
import time
import subprocess
import shutil
from pathlib import Path
import google.generativeai as genai
import tempfile
import uuid
from typing import Optional, List, Dict, Any
from fastapi import File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from datetime import datetime

from ..HelperClass import Agent365Helper
from utils.db_table import insert_office_agent_record

class FileExecutor:
    """Handles file processing and code execution"""
    
    def __init__(self):
        """Initialize the executor with helper class"""
        self.helper = Agent365Helper()
        self.model = self.helper.model
        self.codes_dir = self.helper.codes_dir
        self.temp_dir = self.helper.temp_dir
        # Archive directory to store versioned outputs (fixed path as requested)
        from pathlib import Path as _P
        self.archive_dir = _P("D:/Ricky/Projects/Office_Agent/files")
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_file(
        self,
        file: UploadFile | None,
        prompt: str,
        return_file: bool = False,
        current_user: str = None,
        existing_file_path: str | None = None,
    ) -> Dict[str, Any]:
        """
        Process a file with Gemini AI and optionally return the generated/modified file.
        
        Args:
            file: The uploaded file to process
            prompt: The instruction for what to do with the file
            return_file: Whether to return the generated/modified file as download
            current_user: The username of the current user for logging
            
        Returns:
            Dictionary with processing results
        """
        
        # Determine target file to modify
        timestamp = int(time.time())
        temp_file_path: Path
        original_name: str
        # 1) Explicit existing file path takes precedence
        if existing_file_path:
            provided_path = Path(existing_file_path)
            if not provided_path.exists() or not provided_path.is_file():
                raise HTTPException(status_code=404, detail=f"File not found at path: {existing_file_path}")
            original_name = provided_path.stem
            temp_file_path = provided_path  # modify in place
        # 2) Uploaded file
        elif file is not None:
            original_name = Path(file.filename).stem
            clean_name = "".join(c for c in original_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            file_extension = Path(file.filename).suffix
            # Store uploaded files in archive_dir as requested
            temp_file_path = self.archive_dir / f"{clean_name}_{timestamp}{file_extension}"
        # 3) Fallback to user's last file path
        else:
            if not current_user:
                raise HTTPException(status_code=400, detail="No user context available for last file lookup")
            last_path = self.helper.get_last_file_for_user(current_user)
            if not last_path:
                raise HTTPException(status_code=400, detail="No file provided and no last file found for user")
            provided_path = Path(last_path)
            if not provided_path.exists() or not provided_path.is_file():
                raise HTTPException(status_code=404, detail=f"Last file not found at path: {last_path}")
            original_name = provided_path.stem
            temp_file_path = provided_path
        
        # Initialize logging variables
        start_time = datetime.now()
        status = "SUCCESS"
        remarks = ""
        output_file_path = str(temp_file_path)
        
        try:
            content_size = 0
            if existing_file_path:
                try:
                    content_size = Path(temp_file_path).stat().st_size
                except Exception:
                    content_size = 0
            elif file is not None:
                with open(temp_file_path, "wb") as buffer:
                    content = await file.read()
                    content_size = len(content)
                    buffer.write(content)
            else:
                # Using last file path
                try:
                    content_size = Path(temp_file_path).stat().st_size
                except Exception:
                    content_size = 0
            
            print(f"\n{'='*60}")
            print(f"🚀 STARTING FILE PROCESSING")
            print(f"{'='*60}")
            print(f"📁 File: {str(temp_file_path.name)} (Size: {content_size} bytes)")
            print(f"👤 User: {current_user}")
            print(f"💬 Prompt: {prompt}")
            print(f"⏰ Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            # Log where the file comes from
            if existing_file_path:
                print(f"🛠️ Modifying existing file in-place: {temp_file_path}")
            elif file is not None:
                print(f"💾 Saved to: {temp_file_path}")
            else:
                print(f"♻️ Using user's last file path: {temp_file_path}")
            print(f"{'='*60}")
            
            # Process file content
            file_content = self.helper.process_file_content(str(temp_file_path))
            
            # Build instruction prefix
            instruction_prefix = self.helper.generate_instruction_prefix()
            
            # Generate response
            if isinstance(file_content, str):
                prompt_with_context = (
                    instruction_prefix
                    + "\n\nYou are given the following file content. Write Python code that opens the source document using the appropriate library and directly modifies it to complete the task. Do NOT create separate text files - work directly on the original document.\n"
                    + "CRITICAL: Do NOT use any styles like 'Heading 1', 'Title', 'Normal' - use only plain text without any formatting.\n"
                    + "CRITICAL: You MUST modify the file at TARGET_FILE_PATH directly. Do NOT create new files. Save changes back to TARGET_FILE_PATH.\n"
                    + "CRITICAL: DO NOT use tempfile, shutil.move(), shutil.copy(), or any file copying/moving operations - this causes permission errors when files are open.\n"
                    + "CRITICAL: Open the file, modify it in memory, then save directly to TARGET_FILE_PATH - no intermediate files.\n"
                    + "CRITICAL: If the file is empty (0 bytes), create new content from scratch using the appropriate library.\n\n"
                    f"[FILE CONTENT START]\n{file_content}\n[FILE CONTENT END]\n\n"
                    f"Task: {prompt}\n\n"
                    f"IMPORTANT: The file to modify is at: {temp_file_path}\n"
                    f"Save your changes back to this exact same file path. DO NOT create temp files or copy/move files."
                )
                try:
                    response = self.model.generate_content(prompt_with_context)
                except Exception as gemini_error:
                    print(f"GEMINI ERROR: {gemini_error}")
                    raise HTTPException(status_code=500, detail=f"Gemini API error: {gemini_error}")
            else:
                # For uploaded files to Gemini
                try:
                    response = self.model.generate_content([file_content, instruction_prefix, prompt])
                except Exception as gemini_error:
                    print(f"GEMINI ERROR: {gemini_error}")
                    raise HTTPException(status_code=500, detail=f"Gemini API error: {gemini_error}")
            
            # Extract and save code
            print(f"\n🤖 GEMINI RESPONSE RECEIVED")
            print(f"📝 Response length: {len(response.text or '')} characters")
            code_blocks = self.helper.extract_python_code_blocks(response.text or "")
            print(f"🔍 Extracted {len(code_blocks)} code blocks")
            
            if code_blocks:
                print(f"📋 Code blocks preview:")
                for i, block in enumerate(code_blocks[:3]):  # Show first 3 blocks
                    preview = block[:100].replace('\n', '\\n')
                    print(f"   Block {i+1}: {preview}...")
                if len(code_blocks) > 3:
                    print(f"   ... and {len(code_blocks) - 3} more blocks")
            # Combine code for saving
            combined_code_text = "\n\n\n".join(code_blocks) if code_blocks else ""

            # Save code to file
            output_filename = self.codes_dir / f"gemini_output_{int(time.time())}.py"
            
            # Track validation and correction attempts
            validation_attempts = 0
            validator_corrections = 0  # Times validator asked for corrections
            error_retries = 0  # Times executor retried due to errors
            
            print(f"📊 Correction tracking enabled: Will show all correction attempts during processing")
            
            # Save original file content BEFORE execution for validation
            original_file_content = ""
            try:
                original_file_content = self.helper.process_file_content(str(temp_file_path))
            except Exception as e:
                print(f"⚠️ Warning: Could not read original file content for validation: {e}")
                # If file is empty, use placeholder
                if temp_file_path.stat().st_size == 0:
                    original_file_content = "Empty file - ready for content creation"
            
            with open(output_filename, "w", encoding="utf-8") as f:
                if code_blocks:
                    f.write("\n\n\n".join(code_blocks))
                else:
                    safe_text = (response.text or "").replace('"""', '""')
                    f.write(f'"""Model response saved (no explicit code block detected):\n\n{safe_text}\n"""\n')
            
            # Execute code if available
            result_files = []
            if code_blocks:
                print(f"\n⚡ EXECUTING CODE BLOCKS")
                print(f"🔢 Number of blocks: {len(code_blocks)}")
                try:
                    original_cwd = os.getcwd()
                    # Change to the directory where the target file is located
                    os.chdir(str(temp_file_path.parent))
                    print(f"📁 Changed working directory to: {temp_file_path.parent}")
                    print(f"🎯 Target file: {temp_file_path}")
                    
                    # Ensure dependencies installed
                    deps = self.helper.extract_imports_from_code("\n\n\n".join(code_blocks))
                    if deps:
                        print(f"📦 Ensuring dependencies installed: {deps}")
                        dep_results = self.helper.ensure_dependencies_installed(deps)
                        for pkg, ok, msg in dep_results[:10]:
                            print(f"   {pkg}: {'OK' if ok else 'FAIL'} - {msg}")
                    
                    exec_globals = {
                        "TARGET_FILE_PATH": str(temp_file_path),
                        "OUTPUT_DIR": str(temp_file_path.parent),  # Use the same directory as the input file
                        "CODES_DIR": str(self.codes_dir),
                        "__name__": "__main__",
                    }
                    
                    # Retry loop for execution errors - allow at least 3 retries
                    max_error_retries = 3
                    execution_successful = False
                    current_code_for_exec = "\n\n\n".join(code_blocks)
                    
                    for retry_attempt in range(max_error_retries + 1):  # 0 to max_error_retries (inclusive)
                        try:
                            if retry_attempt == 0:
                                print(f"\n⚡ Executing code (Initial attempt)...")
                            else:
                                print(f"\n⚡ Re-executing corrected code (Retry attempt #{retry_attempt}/{max_error_retries})...")
                            
                            exec(current_code_for_exec, exec_globals)
                            execution_successful = True
                            if retry_attempt == 0:
                                print("✅ Code executed successfully on first attempt")
                            else:
                                print(f"✅ Code executed successfully after {retry_attempt} error correction(s)")
                            break  # Success, exit retry loop
                            
                        except Exception as exec_error:
                            import traceback as _tb
                            err_details = f"{exec_error}\n{_tb.format_exc()}"
                            
                            if retry_attempt < max_error_retries:
                                error_retries += 1
                                print(f"\n❌ EXECUTION ERROR #{error_retries} (Attempt {retry_attempt + 1}/{max_error_retries + 1})")
                                print(f"❌ Execution failed, attempting auto-fix...")
                                print(f"📝 Error details: {err_details[:800]}")
                                
                                # Regenerate code using error - send executor its own code, error, and original task
                                print(f"🔄 Requesting code correction from executor (Error Retry #{error_retries})...")
                                regenerated = self.helper.regenerate_code_from_error(prompt, current_code_for_exec, err_details)
                                
                                if regenerated and regenerated.strip() and regenerated != current_code_for_exec:
                                    print(f"✅ Executor provided corrected code (Error Correction #{error_retries})")
                                    print(f"📊 Total error retries so far: {error_retries}")
                                    
                                    # Save regenerated code
                                    try:
                                        error_fix_filename = self.codes_dir / f"gemini_output_error_fix_{error_retries}_{int(time.time())}.py"
                                        with open(error_fix_filename, "w", encoding="utf-8") as rf:
                                            rf.write(regenerated)
                                        print(f"💾 Corrected code saved to: {error_fix_filename}")
                                    except Exception as e:
                                        print(f"⚠️ Could not save corrected code: {e}")
                                    
                                    # Install deps again if needed
                                    re_deps = self.helper.extract_imports_from_code(regenerated)
                                    if re_deps:
                                        print(f"📦 Ensuring dependencies for regenerated code: {re_deps}")
                                        self.helper.ensure_dependencies_installed(re_deps)
                                    
                                    # Update code for next retry
                                    current_code_for_exec = regenerated
                                    code_blocks = [regenerated]
                                    combined_code_text = regenerated
                                else:
                                    print(f"⚠️ No code regeneration occurred. Will retry with existing code.")
                                    # Continue with same code for next attempt
                            else:
                                # Max retries reached, raise the error
                                error_retries += 1
                                print(f"\n❌ EXECUTION ERROR #{error_retries} (Final attempt {retry_attempt + 1}/{max_error_retries + 1})")
                                print(f"❌ Maximum retry attempts ({max_error_retries}) reached.")
                                print(f"📊 Total error correction attempts: {error_retries}")
                                print(f"📝 Final error details: {err_details[:800]}")
                                raise Exception(f"Execution failed after {error_retries} error correction attempt(s): {exec_error}\n{_tb.format_exc()}")
                    
                    if not execution_successful:
                        raise Exception(f"Code execution failed after {max_error_retries} retry attempts")
                    
                    # VALIDATION: Compare original vs modified file to ensure task was executed correctly
                    # Implement correction loop with validator
                    max_validator_retries = 3  # Allow up to 3 validator-triggered corrections
                    validator_retry_count = 0
                    validation_passed = False
                    
                    while validator_retry_count <= max_validator_retries:
                        print(f"\n🔍 VALIDATING FILE MODIFICATIONS (Validation #{validation_attempts + 1})")
                        validation_attempts += 1
                        modified_file_content = ""
                        try:
                            modified_file_content = self.helper.process_file_content(str(temp_file_path))
                        except Exception as e:
                            print(f"⚠️ Warning: Could not read modified file content for validation: {e}")
                            modified_file_content = "Unable to read modified file content"
                        
                        if original_file_content and modified_file_content:
                            validator_result = self.helper.validate_code_against_task(
                                prompt, 
                                original_file_content, 
                                modified_file_content,
                                combined_code_text
                            )
                            is_valid = validator_result.get("valid", True)
                            feedback = validator_result.get("feedback", "")
                            
                            print(f"🔎 Validator result: {'✅ VALID' if is_valid else '❌ INVALID'}")
                            print(f"📋 Feedback: {feedback[:500]}")
                            
                            if is_valid:
                                validation_passed = True
                                if validator_retry_count > 0:
                                    print(f"✅ Validation passed after {validator_retry_count} correction(s)")
                                break
                            else:
                                # Validator found issues - give executor a chance to correct
                                validator_corrections += 1
                                validator_retry_count += 1
                                print(f"\n⚠️ Validator Correction Opportunity #{validator_corrections}")
                                print(f"   Validator detected issues with file modifications")
                                print(f"   Task: {prompt[:200]}...")
                                print(f"   Feedback: {feedback}")
                                print(f"   📊 Total validator corrections given: {validator_corrections}")
                                
                                if validator_retry_count <= max_validator_retries:
                                    print(f"🔄 Regenerating code based on validator feedback...")
                                    # Regenerate code based on validator feedback
                                    regenerated_code = self.helper.regenerate_code_with_feedback(
                                        prompt, 
                                        combined_code_text, 
                                        feedback
                                    )
                                    if regenerated_code and regenerated_code.strip() and regenerated_code != combined_code_text:
                                        print(f"✅ Code regenerated based on validator feedback (correction #{validator_corrections})")
                                        code_blocks = [regenerated_code]
                                        combined_code_text = regenerated_code
                                        
                                        # Save regenerated code
                                        try:
                                            fix_filename = self.codes_dir / f"gemini_output_validator_fix_{validator_corrections}_{int(time.time())}.py"
                                            with open(fix_filename, "w", encoding="utf-8") as rf:
                                                rf.write(regenerated_code)
                                            print(f"💾 Corrected code saved to: {fix_filename}")
                                        except Exception as e:
                                            print(f"⚠️ Could not save corrected code: {e}")
                                        
                                        # Install dependencies if needed
                                        re_deps = self.helper.extract_imports_from_code(regenerated_code)
                                        if re_deps:
                                            print(f"📦 Ensuring dependencies for regenerated code: {re_deps}")
                                            self.helper.ensure_dependencies_installed(re_deps)
                                        
                                        # Re-execute the corrected code
                                        try:
                                            print(f"\n⚡ RE-EXECUTING CORRECTED CODE (Correction #{validator_corrections})")
                                            exec(regenerated_code, exec_globals)
                                            print(f"✅ Corrected code executed successfully")
                                            # Update original file content for next validation
                                            try:
                                                original_file_content = self.helper.process_file_content(str(temp_file_path))
                                            except Exception as e:
                                                print(f"⚠️ Warning: Could not re-read original file: {e}")
                                        except Exception as exec_error:
                                            import traceback as _tb
                                            err_details = f"{exec_error}\n{_tb.format_exc()}"
                                            print(f"❌ Corrected code execution failed:\n{err_details[:800]}")
                                            # Break the loop since execution failed
                                            break
                                    else:
                                        print(f"⚠️ Code regeneration did not produce new code. Stopping validator loop.")
                                        break
                                else:
                                    print(f"⚠️ Maximum validator retries ({max_validator_retries}) reached. Stopping correction loop.")
                                    break
                        else:
                            # Can't validate without file content, skip validation loop
                            validation_passed = True
                            break
                    
                    if not validation_passed and validator_retry_count > 0:
                        print(f"\n⚠️ VALIDATION SUMMARY: File modifications did not fully pass validation after {validator_corrections} correction attempt(s)")
                    elif validation_passed:
                        print(f"\n✅ VALIDATION SUMMARY: File modifications passed validation")
                        if validator_corrections > 0:
                            print(f"   Corrections applied: {validator_corrections}")
                    
                    # Open the original file that was modified
                    if self.helper.open_file_automatically(temp_file_path):
                        print(f"Opened modified file: {temp_file_path}")
                        print(f"File location: {temp_file_path}")
                        result_files.append(str(temp_file_path))
                    else:
                        print(f"Please manually open: {temp_file_path}")
                        print(f"File exists: {temp_file_path.exists()}")
                        print(f"File size: {temp_file_path.stat().st_size if temp_file_path.exists() else 'N/A'} bytes")
                    
                except Exception as exec_error:
                    import traceback
                    error_details = f"{exec_error}\nTraceback: {traceback.format_exc()}"
                    print(f"\n❌ EXECUTION ERROR: {error_details[:1200]}")
                    print(f"\n📊 CORRECTION ATTEMPTS BEFORE FAILURE:")
                    print(f"   🔍 Validation attempts: {validation_attempts}")
                    print(f"   📝 Validator corrections: {validator_corrections}")
                    print(f"   🔄 Error retries: {error_retries}")
                    print(f"   📈 Total correction attempts: {validator_corrections + error_retries}")
                    # Save error details with code file reference
                    error_message = f"Execution failed: {exec_error}"
                    # The code file is already saved, so we include it in the response
                    response_data = {
                        "success": False,
                        "message": "Execution failed - code saved for debugging",
                        "error": error_message,
                        "error_details": error_details[:2000],
                        "code_saved_to": str(output_filename),
                        "original_task": prompt,
                        "generated_files": result_files,
                        "validation_attempts": validation_attempts,
                        "validator_corrections": validator_corrections,
                        "error_retries": error_retries,
                        "total_corrections": validator_corrections + error_retries
                    }
                    # Log error below in outer except block
                    raise HTTPException(status_code=500, detail=response_data)
                finally:
                    os.chdir(original_cwd)
            
            # Persist last file path for the user (for sequential operations)
            if current_user:
                try:
                    self.helper.set_last_file_for_user(current_user, str(temp_file_path))
                    print(f"🔒 Remembered last file for {current_user}: {temp_file_path}")
                except Exception as _e:
                    print(f"⚠️ Could not remember last file for {current_user}: {_e}")

            # Archive a copy of the edited file and set output_file_path accordingly
            try:
                archive_name = f"{Path(temp_file_path).stem}_{int(time.time())}{Path(temp_file_path).suffix}"
                archive_path = self.archive_dir / archive_name
                shutil.copy2(temp_file_path, archive_path)
                output_file_path = str(archive_path)
                download_link = f"/agent365/files/{archive_name}/download"
                print(f"💾 Archived edited file to: {archive_path}")
            except Exception as arch_err:
                print(f"⚠️ Failed to archive edited file: {arch_err}")
                download_link = None

            # Prepare response
            response_data = {
                "success": True,
                "message": "File processed successfully",
                "gemini_response": response.text,
                "code_saved_to": str(output_filename),
                "generated_files": result_files,
                "validation_attempts": validation_attempts,
                "validator_corrections": validator_corrections,
                "error_retries": error_retries,
                "total_corrections": validator_corrections + error_retries,
                "download_link": download_link if 'download_link' in locals() else None
            }
            
            # Log successful processing to database
            if current_user:
                try:
                    processing_time = (datetime.now() - start_time).total_seconds()
                    remarks = f"Processing completed successfully in {processing_time:.2f} seconds. Generated {len(code_blocks)} code blocks."
                    if download_link:
                        remarks += f" | download: {download_link}"
                    
                    print(f"\n💾 LOGGING TO DATABASE")
                    print(f"👤 User: {current_user}")
                    print(f"⏱️ Processing time: {processing_time:.2f} seconds")
                    print(f"📊 Status: {status}")
                    
                    db_result = insert_office_agent_record(
                        user_id=current_user,
                        chat_name=f"File Processing - {original_name}",
                        input_file_path=str(temp_file_path),
                        output_file_path=output_file_path,
                        query=prompt,
                        remarks=remarks,
                        status=status
                    )
                    
                    if db_result:
                        print(f"✅ Database logging successful")
                    else:
                        print(f"❌ Database logging failed")
                        
                except Exception as db_error:
                    print(f"❌ Database logging error: {db_error}")
                    import traceback
                    print(f"Database error traceback: {traceback.format_exc()}")
            
            # Return file if requested
            if return_file and result_files:
                latest_file = result_files[0]
                return FileResponse(
                    path=latest_file,
                    filename=Path(latest_file).name,
                    media_type='application/octet-stream'
                )
            
            # Print completion summary
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            print(f"\n{'='*60}")
            print(f"✅ PROCESSING COMPLETED SUCCESSFULLY")
            print(f"{'='*60}")
            print(f"⏱️ Total time: {total_time:.2f} seconds")
            print(f"📁 Files processed: {len(result_files)}")
            print(f"\n📊 CORRECTION SUMMARY:")
            print(f"   🔍 Total validation attempts: {validation_attempts}")
            print(f"   📝 Validator corrections given: {validator_corrections}")
            print(f"   🔄 Executor error retries: {error_retries}")
            print(f"   📈 Total correction attempts: {validator_corrections + error_retries}")
            if validator_corrections + error_retries > 0:
                print(f"   ✅ Code was corrected {validator_corrections + error_retries} time(s) during processing")
            print(f"💾 Database logged: {'Yes' if current_user else 'No'}")
            print(f"🎯 Output file: {temp_file_path}")
            print(f"{'='*60}\n")
            
            return response_data
            
        except Exception as e:
            import traceback
            error_details = f"API Error: {str(e)}\nTraceback: {traceback.format_exc()}"
            
            print(f"\n{'='*60}")
            print(f"❌ PROCESSING FAILED")
            print(f"{'='*60}")
            print(f"🚨 Error: {str(e)}")
            print(f"⏱️ Failed after: {(datetime.now() - start_time).total_seconds():.2f} seconds")
            try:
                from pathlib import Path as _P
                file_label = None
                if 'temp_file_path' in locals() and temp_file_path is not None:
                    file_label = _P(str(temp_file_path)).name
                elif 'file' in locals() and file is not None and hasattr(file, 'filename'):
                    file_label = file.filename
                print(f"📁 File: {file_label or 'Unknown'}")
            except Exception:
                print(f"📁 File: Unknown")
            print(f"👤 User: {current_user}")
            print(f"{'='*60}")
            
            # Log error to database
            if current_user:
                try:
                    status = "ERROR"
                    processing_time = (datetime.now() - start_time).total_seconds()
                    remarks = f"Processing failed after {processing_time:.2f} seconds. Error: {str(e)}"
                    if 'archive_path' in locals():
                        try:
                            archive_name = Path(archive_path).name
                            remarks += f" | download: /agent365/files/{archive_name}/download"
                        except Exception:
                            pass
                    
                    print(f"\n💾 LOGGING ERROR TO DATABASE")
                    db_result = insert_office_agent_record(
                        user_id=current_user,
                        chat_name=f"File Processing - {original_name}",
                        input_file_path=str(temp_file_path),
                        output_file_path=output_file_path,
                        query=prompt,
                        remarks=remarks,
                        status=status
                    )
                    
                    if db_result:
                        print(f"✅ Error logged to database")
                    else:
                        print(f"❌ Failed to log error to database")
                        
                except Exception as db_error:
                    print(f"❌ Database error logging failed: {db_error}")
            
            raise HTTPException(status_code=500, detail=error_details)
    
    def list_generated_files(self, current_user: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """List generated files in files directory, filtered by user ownership"""
        from utils.db_table import get_user_files, check_file_ownership
        import os
        
        temp_files = []
        
        if current_user:
            # Get user's files from database
            user_file_paths = get_user_files(current_user)
            user_file_paths_set = set(user_file_paths)
            # Also create a set with normalized paths for comparison
            user_file_paths_normalized = {p.replace("\\", "/") for p in user_file_paths}
            user_file_paths_set.update(user_file_paths_normalized)
            
            # Filter files that belong to the user
            for file_path in self.archive_dir.glob("*"):
                if file_path.is_file():
                    file_path_str = str(file_path)
                    file_path_normalized = file_path_str.replace("\\", "/")
                    
                    # Check if this file belongs to the user
                    if (file_path_str in user_file_paths_set or 
                        file_path_normalized in user_file_paths_set or
                        check_file_ownership(file_path_str, current_user)):
                        temp_files.append({
                            "name": file_path.name,
                            "path": file_path_str,
                            "size": file_path.stat().st_size,
                            "modified": file_path.stat().st_mtime
                        })
        else:
            # No user specified - return empty list for security
            pass
        
        return {"files": temp_files, "user": current_user}
    
    def delete_file(self, filename: str, current_user: str = None) -> Dict[str, str]:
        """Delete a specific file from files directory - only if it belongs to the user"""
        from utils.db_table import check_file_ownership
        from fastapi import HTTPException
        
        file_path = self.archive_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check file ownership if user is specified
        if current_user:
            file_path_str = str(file_path)
            if not check_file_ownership(file_path_str, current_user):
                raise HTTPException(
                    status_code=403, 
                    detail=f"Access denied: File {filename} does not belong to user {current_user}"
                )
        
        try:
            file_path.unlink()
            return {"message": f"File {filename} deleted successfully", "user": current_user}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not delete file: {e}")
    
    def open_file(self, filename: str, current_user: str = None) -> Dict[str, Any]:
        """Manually open a specific file from files directory - only if it belongs to the user"""
        from utils.db_table import check_file_ownership
        from fastapi import HTTPException
        
        file_path = self.archive_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check file ownership if user is specified
        if current_user:
            file_path_str = str(file_path)
            if not check_file_ownership(file_path_str, current_user):
                raise HTTPException(
                    status_code=403, 
                    detail=f"Access denied: File {filename} does not belong to user {current_user}"
                )
        
        try:
            if self.helper.open_file_automatically(file_path):
                return {
                    "message": f"File {filename} opened successfully",
                    "file_path": str(file_path),
                    "file_size": file_path.stat().st_size,
                    "user": current_user
                }
            else:
                raise HTTPException(status_code=500, detail="Could not open file")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not open file: {e}")

    def download_file(self, filename: str, current_user: str = None) -> Dict[str, Any]:
        """Provide a file for download if it belongs to the current user from files directory"""
        from utils.db_table import check_file_ownership
        from fastapi import HTTPException
        from fastapi.responses import FileResponse
        
        file_path = self.archive_dir / filename
        
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Ownership check
        if current_user:
            file_path_str = str(file_path)
            if not check_file_ownership(file_path_str, current_user):
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied: File {filename} does not belong to user {current_user}"
                )
        
        try:
            return FileResponse(path=str(file_path), filename=file_path.name, media_type='application/octet-stream')
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not prepare file for download: {e}")
