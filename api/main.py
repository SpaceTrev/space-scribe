"""FastAPI main application"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
import logging
import time
from pathlib import Path

# Import routers
from api.routes import transcribe, search, export, health

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SpaceScribe API",
    description="Comprehensive YouTube video transcription platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error": str(exc)},
    )


# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(transcribe.router, prefix="/api/v1", tags=["transcribe"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(export.router, prefix="/api/v1", tags=["export"])


# Mount static files for web interface
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

    # Serve the web interface at root
    @app.get("/")
    async def serve_web_interface():
        """Serve the web interface"""
        index_file = web_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        else:
            return {
                "name": "SpaceScribe API",
                "version": "0.1.0",
                "description": "YouTube video transcription platform",
                "docs": "/docs",
                "health": "/api/v1/health",
            }
else:
    # Fallback if web directory doesn't exist
    @app.get("/")
    async def root():
        return {
            "name": "SpaceScribe API",
            "version": "0.1.0",
            "description": "YouTube video transcription platform",
            "docs": "/docs",
            "health": "/api/v1/health",
        }


# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("SpaceScribe API starting up...")
    # Initialize database
    try:
        from database.database import init_db
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("SpaceScribe API shutting down...")
