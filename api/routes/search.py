"""Search endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Transcript, Tag
from sqlalchemy import or_, func
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search")
async def search_transcripts(
    query: str,
    limit: int = 10,
    category: Optional[str] = None,
    language: Optional[str] = None,
    min_quality: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """
    Full-text search across transcripts

    - **query**: Search query
    - **limit**: Maximum results to return
    - **category**: Filter by tag category
    - **language**: Filter by language
    - **min_quality**: Minimum quality score
    """
    try:
        # Build query
        search_query = db.query(Transcript).filter(
            or_(
                Transcript.transcript_full.contains(query),
                Transcript.title.contains(query),
                Transcript.channel_name.contains(query),
            )
        )

        # Apply filters
        if category:
            search_query = (
                search_query.join(Tag)
                .filter(Tag.tag_category == category)
                .distinct()
            )

        if language:
            search_query = search_query.filter(Transcript.language == language)

        if min_quality is not None:
            search_query = search_query.filter(Transcript.quality_score >= min_quality)

        # Execute query
        results = search_query.limit(limit).all()

        return {
            "query": query,
            "total_results": len(results),
            "results": [
                {
                    "video_id": t.video_id,
                    "title": t.title,
                    "channel_name": t.channel_name,
                    "youtube_url": t.youtube_url,
                    "duration_seconds": t.duration_seconds,
                    "language": t.language,
                    "method": t.transcript_method,
                    "quality_score": t.quality_score,
                    "transcript_preview": (
                        t.transcript_full[:200] + "..."
                        if len(t.transcript_full or "") > 200
                        else t.transcript_full
                    ),
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in results
            ],
        }

    except Exception as e:
        logger.error(f"Error in search endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/tags")
async def search_by_tags(
    tags: str,  # Comma-separated tags
    match_all: bool = False,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """
    Search transcripts by tags

    - **tags**: Comma-separated tag names
    - **match_all**: If true, transcript must have all tags; if false, any tag
    - **limit**: Maximum results
    """
    try:
        tag_list = [tag.strip() for tag in tags.split(",")]

        if match_all:
            # Must have all tags
            query = db.query(Transcript)
            for tag_name in tag_list:
                query = query.join(Tag).filter(Tag.tag_name == tag_name)
            results = query.distinct().limit(limit).all()
        else:
            # Must have any tag
            results = (
                db.query(Transcript)
                .join(Tag)
                .filter(Tag.tag_name.in_(tag_list))
                .distinct()
                .limit(limit)
                .all()
            )

        return {
            "tags": tag_list,
            "match_all": match_all,
            "total_results": len(results),
            "results": [
                {
                    "video_id": t.video_id,
                    "title": t.title,
                    "channel_name": t.channel_name,
                    "youtube_url": t.youtube_url,
                }
                for t in results
            ],
        }

    except Exception as e:
        logger.error(f"Error in tag search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/stats")
async def search_statistics(db: Session = Depends(get_db)):
    """Get search and database statistics"""
    try:
        total_transcripts = db.query(func.count(Transcript.id)).scalar()
        total_tags = db.query(func.count(Tag.id)).scalar()
        unique_tags = db.query(func.count(func.distinct(Tag.tag_name))).scalar()

        # Top tags
        top_tags = (
            db.query(Tag.tag_name, func.count(Tag.id).label("count"))
            .group_by(Tag.tag_name)
            .order_by(func.count(Tag.id).desc())
            .limit(20)
            .all()
        )

        # Language distribution
        languages = (
            db.query(Transcript.language, func.count(Transcript.id))
            .group_by(Transcript.language)
            .all()
        )

        return {
            "total_transcripts": total_transcripts,
            "total_tags": total_tags,
            "unique_tags": unique_tags,
            "top_tags": [{"tag": tag, "count": count} for tag, count in top_tags],
            "languages": [{"language": lang, "count": count} for lang, count in languages],
        }

    except Exception as e:
        logger.error(f"Error in search stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
