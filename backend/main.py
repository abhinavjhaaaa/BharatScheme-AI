import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.api.schemes import router as schemes_router
from backend.app.api.chat import router as chat_router
from backend.app.api.eligibility import router as eligibility_router
from backend.app.api.compare import router as compare_router

app = FastAPI(
    title=settings.app_name,
    description="Multilingual NLP-Based Government Scheme Intelligence & Grounded RAG System",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(schemes_router)
app.include_router(chat_router)
app.include_router(eligibility_router)
app.include_router(compare_router)

# Frontend directories
FRONTEND_DIR = PROJECT_ROOT / "frontend"


@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint reporting API and index status.
    """
    faiss_ready = settings.default_faiss_index.exists()
    schemes_ready = settings.schemes_file.exists()

    return {
        "status": "healthy" if (faiss_ready and schemes_ready) else "degraded",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "ollama_model": settings.ollama_model,
        "faiss_index_exists": faiss_ready,
        "schemes_data_exists": schemes_ready,
    }


@app.get("/api", tags=["General"])
def api_root():
    return {
        "message": f"{settings.app_name} API is operational",
        "version": settings.app_version,
        "docs": "/docs",
        "endpoints": [
            "/api/schemes",
            "/api/chat",
            "/api/eligibility",
            "/api/compare",
            "/health",
        ],
    }


# Mount static assets if frontend directory exists
if FRONTEND_DIR.exists():
    # Mount css, js, etc.
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
    if (FRONTEND_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    def serve_frontend_index():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse(
            {"message": f"{settings.app_name} API is running. Frontend index.html not found."}
        )
else:
    @app.get("/", include_in_schema=False)
    def serve_root():
        return {
            "message": f"{settings.app_name} API is running",
            "docs": "/docs",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )