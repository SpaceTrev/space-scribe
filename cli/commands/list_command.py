"""List command"""
from rich.console import Console
from rich.table import Table
from typing import Optional

console = Console()


def run(category: Optional[str], limit: int, sort: str):
    """
    List all transcripts

    Args:
        category: Filter by category
        limit: Maximum results
        sort: Sort field
    """
    from database.database import SessionLocal
    from database.models import Transcript, Tag

    try:
        db = SessionLocal()

        # Build query
        query = db.query(Transcript)

        # Filter by category
        if category:
            query = (
                query.join(Tag)
                .filter(Tag.tag_category == category)
                .distinct()
            )

        # Sort
        if sort == "created_at":
            query = query.order_by(Transcript.created_at.desc())
        elif sort == "title":
            query = query.order_by(Transcript.title)
        elif sort == "duration":
            query = query.order_by(Transcript.duration_seconds.desc())

        transcripts = query.limit(limit).all()

        if not transcripts:
            console.print("\n[yellow]No transcripts found[/yellow]")
            console.print(
                "[dim]Run 'spacescribe transcribe <url>' to create your first transcript[/dim]\n"
            )
            return

        # Create table
        table = Table(title=f"Transcripts ({len(transcripts)} total)")
        table.add_column("Video ID", style="cyan", no_wrap=True)
        table.add_column("Title", style="white", max_width=40)
        table.add_column("Channel", style="blue", max_width=20)
        table.add_column("Duration", style="green", justify="right")
        table.add_column("Method", style="yellow")
        table.add_column("Quality", style="magenta", justify="right")

        for t in transcripts:
            duration_min = t.duration_seconds // 60 if t.duration_seconds else 0
            quality = f"{t.quality_score:.2f}" if t.quality_score else "N/A"

            table.add_row(
                t.video_id or "N/A",
                t.title or "N/A",
                t.channel_name or "N/A",
                f"{duration_min}m",
                t.transcript_method or "N/A",
                quality,
            )

        console.print("\n")
        console.print(table)
        console.print()

        db.close()

    except Exception as e:
        console.print(f"[red]Error listing transcripts: {e}[/red]")
