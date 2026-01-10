"""Health check endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Transcript
from sqlalchemy import func

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "SpaceScribe API",
        "version": "0.1.0",
    }


@router.get("/health/db")
async def database_health(db: Session = Depends(get_db)):
    """Database health check"""
    try:
        # Try to query database
        count = db.query(func.count(Transcript.id)).scalar()
        return {
            "status": "healthy",
            "database": "connected",
            "transcripts_count": count,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }
