from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from RequestHandling.RequestHandling_router import router

# Create FastAPI app
app = FastAPI(
    title="Agent365 API",
    description="AI-powered file processing with Gemini",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router
app.include_router(router)

@app.get("/")
async def root():
    return {
        "message": "Agent365 API is running!",
        "docs": "/docs",
        "endpoints": {
            "process_file": "/agent365/process-file",
            "health": "/agent365/health",
            "list_files": "/agent365/files",
            "delete_file": "/agent365/files/{filename}",
            "open_file": "/agent365/open-file/{filename}",
            "user_management": {
                "list_users": "/agent365/users",
                "add_user": "/agent365/users",
                "remove_user": "/agent365/users/{username}",
                "change_password": "/agent365/users/{username}/password",
                "profile": "/agent365/profile"
            },
            "database": {
                "user_history": "/agent365/history",
                "db_status": "/agent365/db-status"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_api:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True,
        reload_dirs=[".", "RequestHandling"],
        log_level="info"
    )
