"""Export endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Transcript, Chunk, Tag
from typing import Optional
import json
import csv
import io
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/export")
async def export_transcripts(
    format: str = "json",  # json, csv, txt, markdown, llm
    language: Optional[str] = None,
    method: Optional[str] = None,
    min_quality: Optional[float] = None,
    limit: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Export transcripts in various formats

    - **format**: Export format (json/csv/txt/markdown/llm)
    - **language**: Filter by language
    - **method**: Filter by transcription method
    - **min_quality**: Minimum quality score
    - **limit**: Maximum transcripts to export
    """
    try:
        # Build query
        query = db.query(Transcript)

        # Apply filters
        if language:
            query = query.filter(Transcript.language == language)
        if method:
            query = query.filter(Transcript.transcript_method == method)
        if min_quality is not None:
            query = query.filter(Transcript.quality_score >= min_quality)

        # Apply limit
        if limit:
            query = query.limit(limit)

        transcripts = query.all()

        if not transcripts:
            raise HTTPException(status_code=404, detail="No transcripts found")

        # Export based on format
        if format == "json":
            return _export_json(transcripts)
        elif format == "csv":
            return _export_csv(transcripts)
        elif format == "txt":
            return _export_txt(transcripts)
        elif format == "markdown":
            return _export_markdown(transcripts)
        elif format == "llm":
            return _export_llm_training(transcripts)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in export endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{video_id}")
async def export_single_transcript(
    video_id: str,
    format: str = "json",
    include_chunks: bool = True,
    include_tags: bool = True,
    db: Session = Depends(get_db),
):
    """
    Export a single transcript with all associated data

    - **video_id**: Video ID to export
    - **format**: Export format
    - **include_chunks**: Include chunks in export
    - **include_tags**: Include tags in export
    """
    try:
        transcript = (
            db.query(Transcript).filter(Transcript.video_id == video_id).first()
        )

        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")

        # Build export data
        data = {
            "video_id": transcript.video_id,
            "title": transcript.title,
            "channel_name": transcript.channel_name,
            "youtube_url": transcript.youtube_url,
            "duration_seconds": transcript.duration_seconds,
            "language": transcript.language,
            "transcript": transcript.transcript_full,
            "method": transcript.transcript_method,
            "quality_score": transcript.quality_score,
            "created_at": transcript.created_at.isoformat() if transcript.created_at else None,
        }

        # Add chunks if requested
        if include_chunks:
            chunks = (
                db.query(Chunk)
                .filter(Chunk.transcript_id == transcript.id)
                .order_by(Chunk.chunk_index)
                .all()
            )
            data["chunks"] = [
                {
                    "index": c.chunk_index,
                    "text": c.text,
                    "start_time": c.start_time,
                    "end_time": c.end_time,
                    "word_count": c.word_count,
                    "token_count": c.token_count,
                }
                for c in chunks
            ]

        # Add tags if requested
        if include_tags:
            tags = db.query(Tag).filter(Tag.transcript_id == transcript.id).all()
            data["tags"] = [
                {
                    "name": t.tag_name,
                    "category": t.tag_category,
                    "confidence": t.confidence_score,
                }
                for t in tags
            ]

        if format == "json":
            return data
        elif format == "txt":
            return Response(
                content=transcript.transcript_full,
                media_type="text/plain",
                headers={
                    "Content-Disposition": f"attachment; filename={video_id}.txt"
                },
            )
        else:
            return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in single export: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _export_json(transcripts):
    """Export as JSON"""
    data = [
        {
            "video_id": t.video_id,
            "title": t.title,
            "channel_name": t.channel_name,
            "youtube_url": t.youtube_url,
            "language": t.language,
            "transcript": t.transcript_full,
            "duration_seconds": t.duration_seconds,
            "method": t.transcript_method,
            "quality_score": t.quality_score,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in transcripts
    ]
    return data


def _export_csv(transcripts):
    """Export as CSV"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(
        [
            "video_id",
            "title",
            "channel",
            "url",
            "duration",
            "language",
            "method",
            "quality_score",
            "transcript",
        ]
    )

    # Data
    for t in transcripts:
        writer.writerow(
            [
                t.video_id,
                t.title,
                t.channel_name,
                t.youtube_url,
                t.duration_seconds,
                t.language,
                t.transcript_method,
                t.quality_score,
                t.transcript_full,
            ]
        )

    content = output.getvalue()
    output.close()

    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transcripts.csv"},
    )


def _export_txt(transcripts):
    """Export as plain text"""
    lines = []
    for t in transcripts:
        lines.append(f"=== {t.title} ===")
        lines.append(f"Channel: {t.channel_name}")
        lines.append(f"URL: {t.youtube_url}")
        lines.append("")
        lines.append(t.transcript_full or "")
        lines.append("")
        lines.append("=" * 80)
        lines.append("")

    content = "\n".join(lines)

    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=transcripts.txt"},
    )


def _export_markdown(transcripts):
    """Export as Markdown"""
    lines = ["# SpaceScribe Transcripts\n"]

    for t in transcripts:
        lines.append(f"## {t.title}\n")
        lines.append(f"**Channel:** {t.channel_name}\n")
        lines.append(f"**URL:** {t.youtube_url}\n")
        lines.append(f"**Language:** {t.language}\n")
        lines.append(f"**Duration:** {t.duration_seconds // 60 if t.duration_seconds else 0} minutes\n")
        lines.append("\n### Transcript\n")
        lines.append(f"{t.transcript_full}\n")
        lines.append("\n---\n")

    content = "\n".join(lines)

    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=transcripts.md"},
    )


def _export_llm_training(transcripts):
    """Export in LLM training format"""
    data = []

    for t in transcripts:
        conversation = {
            "messages": [
                {
                    "role": "system",
                    "content": f"You are learning from a YouTube video titled '{t.title}' by {t.channel_name}.",
                },
                {
                    "role": "user",
                    "content": f"Please summarize the main points from this video.",
                },
                {"role": "assistant", "content": t.transcript_full or ""},
            ],
            "metadata": {
                "video_id": t.video_id,
                "title": t.title,
                "channel": t.channel_name,
                "url": t.youtube_url,
                "language": t.language,
            },
        }
        data.append(conversation)

    return data
