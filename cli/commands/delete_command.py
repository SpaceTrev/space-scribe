"""Delete command"""
from rich.console import Console
from rich.prompt import Confirm

console = Console()


def run(video_id: str, force: bool):
    """
    Delete a transcript

    Args:
        video_id: Video ID to delete
        force: Skip confirmation
    """
    from database.database import SessionLocal
    from database.models import Transcript

    try:
        db = SessionLocal()

        # Find transcript
        transcript = db.query(Transcript).filter(Transcript.video_id == video_id).first()

        if not transcript:
            console.print(f"\n[red]Transcript not found for video ID: {video_id}[/red]\n")
            db.close()
            return

        # Confirm deletion
        if not force:
            console.print(f"\n[yellow]About to delete:[/yellow]")
            console.print(f"  Title: {transcript.title}")
            console.print(f"  Channel: {transcript.channel_name}")
            console.print(f"  Video ID: {transcript.video_id}\n")

            confirmed = Confirm.ask("Are you sure you want to delete this transcript?")

            if not confirmed:
                console.print("[yellow]Deletion cancelled[/yellow]\n")
                db.close()
                return

        # Delete (cascades to chunks and tags)
        db.delete(transcript)
        db.commit()

        console.print(f"\n[green]Transcript deleted successfully: {video_id}[/green]\n")

        db.close()

    except Exception as e:
        console.print(f"[red]Error deleting transcript: {e}[/red]")
