"""Search command"""
from rich.console import Console
from rich.table import Table
from typing import Optional

console = Console()


def run(query: str, limit: int, category: Optional[str]):
    """
    Search transcripts

    Args:
        query: Search query
        limit: Maximum results
        category: Filter by category
    """
    from database.database import SessionLocal
    from database.models import Transcript, Tag
    from sqlalchemy import or_

    console.print(f"\n[bold cyan]Searching for:[/bold cyan] '{query}'\n")

    try:
        db = SessionLocal()

        # Build query
        query_obj = db.query(Transcript).filter(
            or_(
                Transcript.transcript_full.contains(query),
                Transcript.title.contains(query),
                Transcript.channel_name.contains(query),
            )
        )

        # Filter by category if specified
        if category:
            query_obj = (
                query_obj.join(Tag)
                .filter(Tag.tag_category == category)
                .distinct()
            )

        results = query_obj.limit(limit).all()

        if not results:
            console.print("[yellow]No results found[/yellow]")
            return

        # Display results in table
        table = Table(title=f"Search Results ({len(results)} found)")
        table.add_column("Video ID", style="cyan")
        table.add_column("Title", style="white", max_width=40)
        table.add_column("Channel", style="blue")
        table.add_column("Duration", style="green")

        for transcript in results:
            duration_min = (
                transcript.duration_seconds // 60 if transcript.duration_seconds else 0
            )
            table.add_row(
                transcript.video_id,
                transcript.title or "N/A",
                transcript.channel_name or "N/A",
                f"{duration_min}m",
            )

        console.print(table)

        db.close()

    except Exception as e:
        console.print(f"[red]Error searching: {e}[/red]")
