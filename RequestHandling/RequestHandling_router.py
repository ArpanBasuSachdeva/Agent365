from fastapi import APIRouter
from .API.process_endpoint import router as process_router

# Create main router for RequestHandling
request_handling_router = APIRouter()

# Include all API routes
request_handling_router.include_router(process_router, tags=["File Processing"])
