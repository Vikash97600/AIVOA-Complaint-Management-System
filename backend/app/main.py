import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging_config import setup_logging, logger
from app.core.exceptions import (
    AIVOAException,
    aivoa_exception_handler,
    unhandled_exception_handler,
)
from app.api.router import api_router

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} API in '{settings.ENVIRONMENT}' environment")
    yield
    logger.info(f"Shutting down {settings.APP_NAME} API")

app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="AI-Powered Customer Complaint Management System API for Pharmaceutical Manufacturing QMS",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration allowing React frontend
allowed_origins = [settings.FRONTEND_URL]
if settings.ENVIRONMENT == "development":
    allowed_origins.append("http://localhost:5173")
    allowed_origins.append("http://127.0.0.1:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Request ID & Logging Middleware
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    
    response.headers["X-Request-ID"] = request_id
    logger.info(f"[{request_id}] {request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)")
    return response

# Exception handlers
app.add_exception_handler(AIVOAException, aivoa_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Include central router (/api)
app.include_router(api_router)

@app.get("/", tags=["Root"])
async def root():
    return {
        "system": settings.APP_NAME,
        "industry": "Pharmaceutical Manufacturing",
        "status": "operational",
        "environment": settings.ENVIRONMENT
    }
