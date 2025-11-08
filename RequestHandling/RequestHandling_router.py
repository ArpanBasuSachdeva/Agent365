"""
RequestHandling_router.py - Main FastAPI router for Agent365
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import os
import secrets
from typing import Dict, Any
from datetime import datetime

from .API.executor import FileExecutor
from .HelperClass import Agent365Helper
from utils.db_table import get_user_history, test_database_connection, check_file_ownership, get_user_record_by_id, insert_office_agent_record

# Initialize router
router = APIRouter(prefix="/agent365", tags=["Agent365"])

# Basic Authentication
security = HTTPBasic()

# Initialize helper and executor
helper = Agent365Helper()
executor = FileExecutor()

# Authentication function
def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Authenticate user with multi-user system"""
    if not helper.authenticate_user(credentials.username, credentials.password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@router.post("/process-file")
async def process_file(
    file: UploadFile | None = File(None),
    prompt: str = Form(...),
    return_file: bool = Form(False),
    file_path: str | None = Form(None),
    current_user: str = Depends(get_current_user)
):
    """
    Process a file with Gemini AI and optionally return the generated/modified file.
    
    - **file**: The uploaded file to process (supports .docx, .xlsx, .pptx)
    - **file_path**: A server-accessible absolute path to an existing file to modify directly
    - If neither file nor file_path is provided, the user's last file path is used (if available)
    - **prompt**: The instruction for what to do with the file
    - **return_file**: Whether to return the generated/modified file as download
    """
    resolved_path: str | None = None
    if file_path:
        candidate = file_path.strip()
        if candidate.lower() in {"", "string", "none", "null"}:
            candidate = ""
        if candidate:
            from pathlib import Path
            candidate_path = Path(candidate)
            if not candidate_path.is_absolute():
                candidate_path = executor.archive_dir / candidate
            resolved_path = str(candidate_path)

    return await executor.process_file(file, prompt, return_file, current_user, resolved_path)

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    """Upload a file, save it to server storage, and remember it as the user's current file.
    Does NOT process the file yet. Use /agent365/chat to work on it later.
    """
    # Use executor.helper temp_dir and naming logic similar to executor
    import time
    from pathlib import Path
    timestamp = int(time.time())
    original_name = Path(file.filename).stem
    clean_name = "".join(c for c in original_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    file_extension = Path(file.filename).suffix
    # Save to files directory (archive_dir)
    saved_path = executor.archive_dir / f"{clean_name}_{timestamp}{file_extension}"

    # Save uploaded file
    content = await file.read()
    with open(saved_path, "wb") as buffer:
        buffer.write(content)

    # Remember last file for this user
    executor.helper.set_last_file_for_user(current_user, str(saved_path))
    # Log upload in database to establish ownership
    try:
        download_link = f"/agent365/files/{saved_path.name}/download"
        insert_office_agent_record(
            user_id=current_user,
            chat_name=f"Upload - {original_name}",
            input_file_path=str(saved_path),
            output_file_path=str(saved_path),
            query="UPLOAD",
            remarks=f"File uploaded and stored in files directory | download: {download_link}",
            status="UPLOADED"
        )
    except Exception:
        pass
    return {
        "message": "File uploaded successfully",
        "filename": saved_path.name,
        "size": len(content),
        "saved_path": str(saved_path),
        "download_link": download_link
    }

@router.post("/chat")
async def chat_on_file(
    prompt: str = Form(...),
    filename: str = Form(...),
    return_file: bool = Form(False),
    current_user: str = Depends(get_current_user)
):
    """Work on a previously uploaded file chosen via dropdown (filename from user's files directory)."""
    from pathlib import Path
    # Ensure chat operates on files stored under the fixed files directory
    candidate = executor.archive_dir / filename
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Selected file not found on server")
    if not check_file_ownership(str(candidate), current_user):
        raise HTTPException(status_code=403, detail="Access denied: You do not own this file")

    return await executor.process_file(
        file=None,
        prompt=prompt,
        return_file=return_file,
        current_user=current_user,
        existing_file_path=str(candidate),
    )

@router.get("/health")
async def health_check(current_user: str = Depends(get_current_user)):
    """Health check endpoint"""
    return {"status": "healthy", "service": "Agent365", "user": current_user}

@router.get("/files")
async def list_generated_files(current_user: str = Depends(get_current_user)):
    """List generated files in files directory - only shows files belonging to the current user"""
    return executor.list_generated_files(current_user)

@router.delete("/files/{filename}")
async def delete_file(filename: str, current_user: str = Depends(get_current_user)):
    """Delete a specific file from files directory - only if it belongs to the current user"""
    return executor.delete_file(filename, current_user)

@router.post("/open-file/{filename}")
async def open_file(filename: str, current_user: str = Depends(get_current_user)):
    """Manually open a specific file from files directory - only if it belongs to the current user"""
    return executor.open_file(filename, current_user)

@router.get("/files/{filename}/download")
async def download_file(filename: str, current_user: str = Depends(get_current_user)):
    """Download a specific file from files directory - only if it belongs to the current user"""
    return executor.download_file(filename, current_user)

# User Management Endpoints
@router.get("/users")
async def list_users(current_user: str = Depends(get_current_user)):
    """List all users (admin only)"""
    user_info = helper.get_user_info(current_user)
    if not user_info or user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {"users": helper.list_users()}

@router.post("/users")
async def add_user(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("user"),
    current_user: str = Depends(get_current_user)
):
    """Add a new user (admin only)"""
    user_info = helper.get_user_info(current_user)
    if not user_info or user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if helper.add_user(username, password, role):
        return {"message": f"User {username} added successfully"}
    else:
        raise HTTPException(status_code=400, detail="User already exists")

@router.delete("/users/{username}")
async def remove_user(username: str, current_user: str = Depends(get_current_user)):
    """Remove a user (admin only)"""
    user_info = helper.get_user_info(current_user)
    if not user_info or user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if username == current_user:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    if helper.remove_user(username):
        return {"message": f"User {username} removed successfully"}
    else:
        raise HTTPException(status_code=404, detail="User not found")

@router.put("/users/{username}/password")
async def change_password(
    username: str,
    old_password: str = Form(...),
    new_password: str = Form(...),
    current_user: str = Depends(get_current_user)
):
    """Change user password"""
    # Users can only change their own password, admins can change any password
    user_info = helper.get_user_info(current_user)
    if username != current_user and (not user_info or user_info.get("role") != "admin"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if helper.change_password(username, old_password, new_password):
        return {"message": f"Password changed successfully for {username}"}
    else:
        raise HTTPException(status_code=400, detail="Invalid credentials or user not found")

@router.get("/profile")
async def get_profile(current_user: str = Depends(get_current_user)):
    """Get current user profile"""
    user_info = helper.get_user_info(current_user)
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"username": current_user, **user_info}

@router.get("/history")
async def get_user_processing_history(
    limit: int = 10,
    current_user: str = Depends(get_current_user)
):
    """Get user's file processing history from database"""
    try:
        history = get_user_history(current_user, limit)
        return {
            "user": current_user,
            "history": history,
            "total_records": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not fetch history: {e}")

@router.get("/db-status")
async def check_database_status(current_user: str = Depends(get_current_user)):
    """Check database connection status"""
    try:
        is_connected = test_database_connection()
        return {
            "database_connected": is_connected,
            "user": current_user,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "database_connected": False,
            "error": str(e),
            "user": current_user,
            "timestamp": datetime.now().isoformat()
        }

@router.get("/versions")
async def list_versions(
    limit: int = 25,
    filename: str | None = None,
    current_user: str = Depends(get_current_user)
):
    """List archived versions for the current user. Optionally filter by filename (substring match)."""
    try:
        history = get_user_history(current_user, limit)
        print(f"🔍 Versions query: user={current_user}, limit={limit}, filename={filename}, found {len(history)} records")
        
        if filename:
            try:
                from pathlib import Path
                # Extract base name from filename parameter (remove extension for flexible matching)
                filename_base = Path(filename).stem.lower()
                filename_full = filename.lower()
                print(f"🔍 Filtering by filename: base='{filename_base}', full='{filename_full}'")
                
                filtered = []
                for rec in history:
                    # Check both input_file and output_file paths
                    input_path = rec.get("input_file") or ""
                    output_path = rec.get("output_file") or ""
                    
                    # Get base names for comparison
                    input_base = Path(input_path).stem.lower() if input_path else ""
                    output_base = Path(output_path).stem.lower() if output_path else ""
                    input_name = Path(input_path).name.lower() if input_path else ""
                    output_name = Path(output_path).name.lower() if output_path else ""
                    
                    # Match if filename_base is at the start of either base name, or if full filename is in either name
                    # This handles cases like: filename="try2_1762604694.docx" matching "try2_1762604694_1762605007.docx"
                    matches = (
                        input_base.startswith(filename_base) or
                        output_base.startswith(filename_base) or
                        filename_full in input_name or
                        filename_full in output_name or
                        filename_base in input_base or
                        filename_base in output_base
                    )
                    
                    if matches:
                        filtered.append(rec)
                        print(f"✅ Matched record ID {rec.get('id')}: output='{output_name}'")
                    else:
                        print(f"❌ No match for record ID {rec.get('id')}: input='{input_name}', output='{output_name}'")
                
                print(f"📊 Filtered {len(filtered)} records from {len(history)} total")
                history = filtered
            except Exception as filter_error:
                print(f"❌ Error filtering versions by filename: {filter_error}")
                import traceback
                traceback.print_exc()
                # Return empty list if filtering fails
                history = []
    except Exception as e:
        print(f"Error fetching versions: {e}")
        raise HTTPException(status_code=500, detail=f"Could not fetch versions: {e}")
    
    return {"user": current_user, "versions": history}

@router.get("/user-files")
async def list_user_files(current_user: str = Depends(get_current_user)):
    """List files under the files directory that belong to the current user."""
    from pathlib import Path
    files_dir = executor.archive_dir
    results = []
    # Build a set of known user paths from DB (normalized both ways)
    try:
        user_paths = set()
        for rec in get_user_history(current_user, 1000):
            p1 = (rec.get("input_file") or "").replace("\\", "/")
            p2 = (rec.get("output_file") or "").replace("\\", "/")
            if p1:
                user_paths.add(p1)
            if p2:
                user_paths.add(p2)
    except Exception:
        user_paths = set()
    # Include last file even if not in DB
    try:
        last_path = helper.get_last_file_for_user(current_user)
        if last_path:
            user_paths.add(last_path.replace("\\", "/"))
    except Exception:
        pass

    for fp in files_dir.glob("*"):
        if fp.is_file():
            fp_str = str(fp)
            fp_norm = fp_str.replace("\\", "/")
            if fp_norm in user_paths or check_file_ownership(fp_str, current_user):
                download_link = f"/agent365/files/{fp.name}/download"
                results.append({
                    "name": fp.name,
                    "path": fp_str,
                    "size": fp.stat().st_size,
                    "modified": fp.stat().st_mtime,
                    "download_link": download_link
                })
    return {"user": current_user, "files": results}

@router.post("/rollback")
async def rollback_version(
    filename: str = Form(...),
    record_id: int = Form(...),
    current_user: str = Depends(get_current_user)
):
    """Rollback the selected working file (by filename in files directory) to a previous archived version by record id."""
    from pathlib import Path
    import shutil as _shutil

    # Resolve working file and check ownership
    working_file = executor.archive_dir / filename
    if not working_file.exists() or not working_file.is_file():
        raise HTTPException(status_code=404, detail="Working file not found")
    if not check_file_ownership(str(working_file), current_user):
        # If the working file path isn't in DB yet, still restrict to user files directory
        raise HTTPException(status_code=403, detail="Access denied: You do not own this file")

    # Fetch record and validate ownership
    rec = get_user_record_by_id(current_user, record_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Version record not found for this user")
    version_path = rec.get("output_file")
    if not version_path:
        raise HTTPException(status_code=400, detail="Selected version has no output file path")
    vp = Path(version_path)
    if not vp.exists() or not vp.is_file():
        raise HTTPException(status_code=404, detail="Archived version file not found on server")

    # Replace working file with archived version
    restored = False
    try:
        if vp.resolve() == working_file.resolve():
            # Already the same file; nothing to copy
            restored = True
        else:
            _shutil.copy2(vp, working_file)
            restored = True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rollback failed: {e}")

    # Remember for user convenience
    try:
        helper.set_last_file_for_user(current_user, str(working_file))
    except Exception:
        pass

    opened_working = False
    opened_version = False
    try:
        opened_working = helper.open_file_automatically(working_file)
    except Exception:
        opened_working = False
    try:
        # If the archived version is different, try opening it too for reference
        if vp.resolve() != working_file.resolve():
            opened_version = helper.open_file_automatically(vp)
        else:
            opened_version = opened_working
    except Exception:
        opened_version = False

    return {
        "message": "Rollback successful" if restored else "Rollback skipped (already at selected version)",
        "working_file": str(working_file),
        "restored_from": str(vp),
        "record_id": record_id,
        "file_opened": opened_working,
        "version_opened": opened_version
    }
