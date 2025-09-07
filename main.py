import os
import secrets
from typing import Dict
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv
from RequestHandling.RequestHandling_router import request_handling_router

load_dotenv()
security = HTTPBasic()

def _load_users_from_env() -> Dict[str, str]:
    users: Dict[str, str] = {}
    # Simple convention: BASIC_AUTH_USERS is a comma-separated list of usernames
    # For each username U, read BASIC_AUTH_PASS_U as the password
    users_csv = os.getenv("BASIC_AUTH_USERS", "")
    for raw_name in [u.strip() for u in users_csv.split(",") if u.strip()]:
        env_key = f"BASIC_AUTH_PASS_{raw_name}"
        pwd = os.getenv(env_key)
        if pwd is not None:
            users[raw_name] = pwd
    # Backward compatibility with single-user env vars
    single_user = os.getenv("BASIC_AUTH_USER")
    single_pass = os.getenv("BASIC_AUTH_PASS")
    if single_user and single_pass and single_user not in users:
        users[single_user] = single_pass
    # Default fallback if nothing provided
    if not users:
        users["admin"] = "change-me"
    return users

def verify_basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    users = _load_users_from_env()
    provided_username = credentials.username
    provided_password = credentials.password
    if provided_username not in users or not secrets.compare_digest(provided_password, users[provided_username]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

app = FastAPI(dependencies=[Depends(verify_basic_auth)])

# Include the RequestHandling router
app.include_router(request_handling_router)