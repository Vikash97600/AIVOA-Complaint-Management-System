from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Customer Complaint Management System API for Pharmaceutical Manufacturing",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
async def root():
    return {
        "system": settings.APP_NAME,
        "industry": "Pharmaceutical Manufacturing",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.APP_NAME
    }
