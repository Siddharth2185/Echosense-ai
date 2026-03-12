"""
FastAPI main application for Echosense AI
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn

from config import get_settings
from database.connection import init_db

# Import API routers
from api import upload, processing, analytics, training, delete, auth

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("[STARTUP] Starting Echosense AI Backend...")
    init_db()
    print("[OK] Database initialized")
    yield
    # Shutdown
    print("[SHUTDOWN] Shutting down Echosense AI Backend...")


app = FastAPI(
    title="Echosense AI",
    description="Intelligent Call Monitoring AI System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (frontend)
import os
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path, html=True), name="static")

# Mount storage for local development
storage_path = os.path.join(os.path.dirname(__file__), "..", "storage")
if not os.path.exists(storage_path):
    os.makedirs(storage_path)
app.mount("/storage", StaticFiles(directory=storage_path), name="storage")

# Mount uploads directory
uploads_path = os.path.join(os.path.dirname(__file__), "uploads")
if not os.path.exists(uploads_path):
    os.makedirs(uploads_path)
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")


# Include API routers
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(processing.router, prefix="/api/processing", tags=["Processing"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(training.router, prefix="/api/training", tags=["Training"])
app.include_router(delete.router, prefix="/api/calls", tags=["Calls"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Echosense AI",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=settings.debug
    )
