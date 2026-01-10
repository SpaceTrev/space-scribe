"""Transcription endpoints"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from database.database import get_db
from database.models import Transcript, Chunk, Tag
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response models
class TranscribeRequest(BaseModel):
    url: str
    method: Optional[str] = "auto"
    language: Optional[str] = None
    save_to_db: bool = True
    process_nlp: bool = True
    extract_trading: bool = True


class BatchTranscribeRequest(BaseModel):
    urls: List[str]
    method: Optional[str] = "auto"
    parallel: int = 1


class TranscriptResponse(BaseModel):
    video_id: str
    title: Optional[str]
    channel_name: Optional[str]
    duration_seconds: Optional[int]
    language: Optional[str]
    method: str
    quality_score: Optional[float]
    transcript_preview: str
    created_at: Optional[str]

    class Config:
        from_attributes = True


@router.post("/transcribe")
async def transcribe_video(
    request: TranscribeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Transcribe a single YouTube video

    - **url**: YouTube video URL or ID
    - **method**: Transcription method (auto/api/whisper)
    - **language**: Preferred language code
    - **save_to_db**: Save to database
    - **process_nlp**: Run NLP processing
    - **extract_trading**: Extract trading concepts
    """
    try:
        from core.transcriber.transcriber import Transcriber
        from core.processor.nlp_processor import NLPProcessor
        from core.processor.trading_processor import TradingProcessor
        from core.chunker.chunker import Chunker

        # Initialize transcriber
        transcriber = Transcriber(default_method=request.method)

        # Transcribe
        result = transcriber.transcribe(request.url, method=request.method, language=request.language)

        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=f"Transcription failed: {result.get('message', 'Unknown error')}",
            )

        # Process with NLP if requested
        if request.process_nlp:
            nlp_processor = NLPProcessor()
            result["nlp"] = nlp_processor.process_transcript(result["full_text"])

        # Extract trading concepts if requested
        if request.extract_trading:
            trading_processor = TradingProcessor()
            result["trading"] = trading_processor.process_trading_content(result["full_text"])

        # Create chunks
        chunker = Chunker()
        result["chunks"] = chunker.chunk_transcript(
            result["transcript"], result["full_text"]
        )

        # Save to database if requested
        if request.save_to_db:
            _save_transcript_to_db(result, db)

        return {
            "success": True,
            "video_id": result.get("video_id"),
            "method": result.get("method"),
            "language": result.get("language"),
            "quality_score": result.get("quality_score"),
            "transcript_length": len(result.get("full_text", "")),
            "chunks_count": len(result.get("chunks", [])),
            "message": "Transcription completed successfully",
        }

    except Exception as e:
        logger.error(f"Error in transcribe endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_transcribe(
    request: BatchTranscribeRequest,
    background_tasks: BackgroundTasks,
):
    """
    Batch transcribe multiple videos

    - **urls**: List of YouTube URLs
    - **method**: Transcription method
    - **parallel**: Number of parallel workers
    """
    try:
        from core.transcriber.transcriber import Transcriber

        transcriber = Transcriber(default_method=request.method)

        # For now, process sequentially
        # TODO: Implement proper background job processing with Celery
        results = []
        for url in request.urls:
            try:
                result = transcriber.transcribe(url)
                results.append(
                    {
                        "url": url,
                        "success": result.get("success", False),
                        "video_id": result.get("video_id"),
                    }
                )
            except Exception as e:
                results.append({"url": url, "success": False, "error": str(e)})

        successful = sum(1 for r in results if r.get("success"))

        return {
            "total": len(request.urls),
            "successful": successful,
            "failed": len(request.urls) - successful,
            "results": results,
        }

    except Exception as e:
        logger.error(f"Error in batch endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transcripts/{video_id}")
async def get_transcript(video_id: str, db: Session = Depends(get_db)):
    """Get transcript by video ID"""
    transcript = (
        db.query(Transcript).filter(Transcript.video_id == video_id).first()
    )

    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    return {
        "video_id": transcript.video_id,
        "title": transcript.title,
        "channel_name": transcript.channel_name,
        "youtube_url": transcript.youtube_url,
        "duration_seconds": transcript.duration_seconds,
        "language": transcript.language,
        "method": transcript.transcript_method,
        "quality_score": transcript.quality_score,
        "transcript": transcript.transcript_full,
        "created_at": transcript.created_at.isoformat() if transcript.created_at else None,
    }


@router.get("/transcripts")
async def list_transcripts(
    skip: int = 0,
    limit: int = 20,
    language: Optional[str] = None,
    method: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all transcripts with optional filters"""
    query = db.query(Transcript)

    # Apply filters
    if language:
        query = query.filter(Transcript.language == language)
    if method:
        query = query.filter(Transcript.transcript_method == method)

    # Get total count
    total = query.count()

    # Apply pagination
    transcripts = query.order_by(Transcript.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "transcripts": [
            {
                "video_id": t.video_id,
                "title": t.title,
                "channel_name": t.channel_name,
                "duration_seconds": t.duration_seconds,
                "language": t.language,
                "method": t.transcript_method,
                "quality_score": t.quality_score,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in transcripts
        ],
    }


@router.delete("/transcripts/{video_id}")
async def delete_transcript(video_id: str, db: Session = Depends(get_db)):
    """Delete a transcript"""
    transcript = (
        db.query(Transcript).filter(Transcript.video_id == video_id).first()
    )

    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    db.delete(transcript)
    db.commit()

    return {"success": True, "message": f"Transcript {video_id} deleted"}


def _save_transcript_to_db(result: dict, db: Session):
    """Save transcript result to database"""
    try:
        metadata = result.get("metadata", {})

        # Create transcript
        transcript = Transcript(
            video_id=metadata.get("id"),
            youtube_url=metadata.get("webpage_url"),
            title=metadata.get("title"),
            channel_name=metadata.get("channel_name"),
            channel_id=metadata.get("channel_id"),
            upload_date=metadata.get("upload_date"),
            duration_seconds=metadata.get("duration_seconds"),
            view_count=metadata.get("view_count"),
            transcript_full=result.get("full_text"),
            transcript_method=result.get("method"),
            language=result.get("language"),
            quality_score=result.get("quality_score"),
            metadata_json=metadata,
            nlp_processed=True,
            chunks_created=True,
            tags_extracted=True,
        )

        db.add(transcript)
        db.flush()

        # Add chunks
        for chunk in result.get("chunks", []):
            chunk_record = Chunk(
                transcript_id=transcript.id,
                chunk_index=chunk["chunk_index"],
                text=chunk["text"],
                start_time=chunk["start_time"],
                end_time=chunk["end_time"],
                word_count=chunk["word_count"],
                token_count=chunk["token_count"],
                strategy=chunk["strategy"],
                metadata_json=chunk.get("metadata_json", {}),
            )
            db.add(chunk_record)

        # Add NLP tags
        nlp = result.get("nlp", {})
        for entity in nlp.get("entities", [])[:50]:
            tag = Tag(
                transcript_id=transcript.id,
                tag_name=entity["text"],
                tag_category="entity",
                entity_type=entity["label"],
                confidence_score=0.8,
                metadata_json=entity,
            )
            db.add(tag)

        # Add trading tags
        trading = result.get("trading", {})
        for category in ["indicators", "strategies", "instruments"]:
            for item in trading.get(category, [])[:10]:
                tag = Tag(
                    transcript_id=transcript.id,
                    tag_name=item["concept"],
                    tag_category=f"trading_{category[:-1]}",
                    confidence_score=min(1.0, item["mentions"] / 10),
                    metadata_json=item,
                )
                db.add(tag)

        db.commit()
        logger.info(f"Saved transcript to database: {transcript.video_id}")

    except Exception as e:
        db.rollback()
        logger.error(f"Error saving to database: {e}", exc_info=True)
        raise
