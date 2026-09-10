from fastapi import APIRouter
from app.api.routes import health, complaints, copilot

api_router = APIRouter(prefix="/api")

api_router.include_router(health.router)
api_router.include_router(complaints.router)
api_router.include_router(copilot.router)
