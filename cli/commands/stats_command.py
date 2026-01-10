"""Stats command"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def run():
    """Show database statistics"""
    from database.database import SessionLocal
    from database.models import Transcript, Chunk, Tag
    from sqlalchemy import func

    try:
        db = SessionLocal()

        # Get counts
        total_transcripts = db.query(func.count(Transcript.id)).scalar()
        total_chunks = db.query(func.count(Chunk.id)).scalar()
        total_tags = db.query(func.count(Tag.id)).scalar()

        # Get total duration
        total_duration = (
            db.query(func.sum(Transcript.duration_seconds)).scalar() or 0
        )
        total_hours = total_duration / 3600

        # Get method breakdown
        method_stats = (
            db.query(
                Transcript.transcript_method,
                func.count(Transcript.id),
            )
            .group_by(Transcript.transcript_method)
            .all()
        )

        # Get language breakdown
        language_stats = (
            db.query(
                Transcript.language,
                func.count(Transcript.id),
            )
            .group_by(Transcript.language)
            .limit(5)
            .all()
        )

        # Get average quality
        avg_quality = db.query(func.avg(Transcript.quality_score)).scalar() or 0

        # Display overview
        overview = f"""
[bold cyan]Total Transcripts:[/bold cyan] {total_transcripts}
[bold cyan]Total Chunks:[/bold cyan] {total_chunks}
[bold cyan]Total Tags:[/bold cyan] {total_tags}
[bold cyan]Total Duration:[/bold cyan] {total_hours:.1f} hours
[bold cyan]Average Quality:[/bold cyan] {avg_quality:.2f}
        """

        console.print("\n")
        console.print(Panel(overview.strip(), title="Database Statistics", border_style="cyan"))

        # Method breakdown
        if method_stats:
            console.print("\n[bold]Transcription Methods:[/bold]")
            method_table = Table(show_header=False)
            method_table.add_column("Method", style="cyan")
            method_table.add_column("Count", style="white", justify="right")

            for method, count in method_stats:
                method_table.add_row(method or "Unknown", str(count))

            console.print(method_table)

        # Language breakdown
        if language_stats:
            console.print("\n[bold]Top Languages:[/bold]")
            lang_table = Table(show_header=False)
            lang_table.add_column("Language", style="cyan")
            lang_table.add_column("Count", style="white", justify="right")

            for lang, count in language_stats:
                lang_table.add_row(lang or "Unknown", str(count))

            console.print(lang_table)

        console.print()

        db.close()

    except Exception as e:
        console.print(f"[red]Error getting statistics: {e}[/red]")
