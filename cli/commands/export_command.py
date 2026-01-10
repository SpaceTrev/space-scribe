"""Export command"""
from rich.console import Console
from typing import Optional
from pathlib import Path
import json
import csv

console = Console()


def run(format: str, output: Optional[str], filter: Optional[str]):
    """
    Export transcripts in various formats

    Args:
        format: Export format
        output: Output file path
        filter: Filter expression
    """
    from database.database import SessionLocal
    from database.models import Transcript

    console.print(f"\n[bold cyan]Exporting transcripts as {format}[/bold cyan]\n")

    try:
        db = SessionLocal()

        # Get all transcripts (apply filter if specified)
        query = db.query(Transcript)

        if filter:
            # Simple filter parsing (e.g., "language=en")
            if "=" in filter:
                key, value = filter.split("=", 1)
                if hasattr(Transcript, key):
                    query = query.filter(getattr(Transcript, key) == value)

        transcripts = query.all()

        if not transcripts:
            console.print("[yellow]No transcripts found[/yellow]")
            db.close()
            return

        console.print(f"[green]Found {len(transcripts)} transcripts[/green]\n")

        # Determine output path
        if not output:
            output = f"spacescribe_export.{format}"

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Export based on format
        if format == "json":
            _export_json(transcripts, output_path)
        elif format == "csv":
            _export_csv(transcripts, output_path)
        elif format == "txt":
            _export_txt(transcripts, output_path)
        elif format == "markdown":
            _export_markdown(transcripts, output_path)
        elif format == "llm":
            _export_llm_training(transcripts, output_path)
        else:
            console.print(f"[red]Unsupported format: {format}[/red]")
            db.close()
            return

        console.print(f"[green]Exported to: {output_path}[/green]")
        db.close()

    except Exception as e:
        console.print(f"[red]Error exporting: {e}[/red]")


def _export_json(transcripts, output_path):
    """Export as JSON"""
    data = []
    for t in transcripts:
        data.append(
            {
                "video_id": t.video_id,
                "title": t.title,
                "channel": t.channel_name,
                "url": t.youtube_url,
                "language": t.language,
                "transcript": t.transcript_full,
                "duration": t.duration_seconds,
                "method": t.transcript_method,
                "quality_score": t.quality_score,
            }
        )

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)


def _export_csv(transcripts, output_path):
    """Export as CSV"""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "video_id",
                "title",
                "channel",
                "duration",
                "language",
                "method",
                "quality_score",
                "transcript",
            ]
        )

        for t in transcripts:
            writer.writerow(
                [
                    t.video_id,
                    t.title,
                    t.channel_name,
                    t.duration_seconds,
                    t.language,
                    t.transcript_method,
                    t.quality_score,
                    t.transcript_full,
                ]
            )


def _export_txt(transcripts, output_path):
    """Export as plain text"""
    with open(output_path, "w", encoding="utf-8") as f:
        for t in transcripts:
            f.write(f"=== {t.title} ===\n")
            f.write(f"Channel: {t.channel_name}\n")
            f.write(f"URL: {t.youtube_url}\n\n")
            f.write(f"{t.transcript_full}\n\n")
            f.write("=" * 80 + "\n\n")


def _export_markdown(transcripts, output_path):
    """Export as Markdown"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# SpaceScribe Transcripts\n\n")

        for t in transcripts:
            f.write(f"## {t.title}\n\n")
            f.write(f"**Channel:** {t.channel_name}\n")
            f.write(f"**URL:** {t.youtube_url}\n")
            f.write(f"**Language:** {t.language}\n")
            f.write(f"**Duration:** {t.duration_seconds // 60} minutes\n\n")
            f.write("### Transcript\n\n")
            f.write(f"{t.transcript_full}\n\n")
            f.write("---\n\n")


def _export_llm_training(transcripts, output_path):
    """Export in LLM training format"""
    data = []

    for t in transcripts:
        # Create conversation format
        conversation = {
            "messages": [
                {
                    "role": "system",
                    "content": f"You are learning from a YouTube video titled '{t.title}' by {t.channel_name}.",
                },
                {
                    "role": "user",
                    "content": f"Please summarize the main points from this video about {t.title}.",
                },
                {"role": "assistant", "content": t.transcript_full},
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

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
