from fastapi import FastAPI
from RequestHandling.RequestHandling_router import request_handling_router

app = FastAPI()

# Include the RequestHandling router
app.include_router(request_handling_router) 