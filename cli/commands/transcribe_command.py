"""Transcribe command implementation"""
import json
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.table import Table
from typing import Optional
import sys

console = Console()


def run(
    url: str,
    method: Optional[str],
    language: Optional[str],
    save: bool,
    output: Optional[str],
    format: str,
):
    """
    Transcribe a YouTube video

    Args:
        url: YouTube URL or video ID
        method: Transcription method
        language: Language code
        save: Whether to save to database
        output: Output file path
        format: Output format
    """
    from core.transcriber.transcriber import Transcriber
    from core.processor.nlp_processor import NLPProcessor
    from core.processor.trading_processor import TradingProcessor
    from core.chunker.chunker import Chunker

    console.print(f"\n[bold cyan]Transcribing video:[/bold cyan] {url}\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        # Initialize transcriber
        task1 = progress.add_task("[cyan]Initializing transcriber...", total=None)
        transcriber = Transcriber(default_method=method or "auto")
        progress.update(task1, completed=True)

        # Transcribe video
        task2 = progress.add_task("[cyan]Transcribing video...", total=None)
        result = transcriber.transcribe(url, method=method, language=language)
        progress.update(task2, completed=True)

        if not result.get("success"):
            console.print(
                f"\n[red]Transcription failed:[/red] {result.get('message', 'Unknown error')}"
            )
            sys.exit(1)

        # Process with NLP if enabled
        task3 = progress.add_task("[cyan]Processing with NLP...", total=None)
        nlp_processor = NLPProcessor()
        nlp_result = nlp_processor.process_transcript(result["full_text"])
        result["nlp"] = nlp_result
        progress.update(task3, completed=True)

        # Extract trading concepts
        task4 = progress.add_task("[cyan]Extracting trading concepts...", total=None)
        trading_processor = TradingProcessor()
        trading_result = trading_processor.process_trading_content(result["full_text"])
        result["trading"] = trading_result
        progress.update(task4, completed=True)

        # Create chunks
        task5 = progress.add_task("[cyan]Creating chunks...", total=None)
        chunker = Chunker()
        chunks = chunker.chunk_transcript(
            result["transcript"], result["full_text"], strategy="token_based"
        )
        result["chunks"] = chunks
        progress.update(task5, completed=True)

    # Display results
    _display_results(result)

    # Save to database if requested
    if save:
        _save_to_database(result)

    # Save to file if output specified
    if output:
        _save_to_file(result, output, format)

    console.print("\n[green]Transcription complete![/green]")


def _display_results(result: dict):
    """Display transcription results"""
    metadata = result.get("metadata", {})

    # Create info table
    table = Table(title="Video Information", show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Title", metadata.get("title", "N/A"))
    table.add_row("Channel", metadata.get("channel_name", "N/A"))
    table.add_row("Duration", f"{metadata.get('duration_seconds', 0) // 60} minutes")
    table.add_row("Language", result.get("language", "N/A"))
    table.add_row("Method", result.get("method", "N/A"))
    table.add_row("Quality Score", f"{result.get('quality_score', 0):.2f}")

    console.print("\n")
    console.print(table)

    # Display transcript preview
    full_text = result.get("full_text", "")
    preview = full_text[:500] + "..." if len(full_text) > 500 else full_text

    console.print("\n[bold]Transcript Preview:[/bold]")
    console.print(Panel(preview, border_style="blue"))

    # Display NLP insights
    nlp = result.get("nlp", {})
    if nlp:
        console.print("\n[bold]NLP Insights:[/bold]")
        console.print(f"  • Entities: {nlp.get('statistics', {}).get('unique_entities', 0)}")
        console.print(f"  • Keywords: {len(nlp.get('keywords', []))}")
        console.print(f"  • Topics: {len(nlp.get('topics', []))}")

        # Top keywords
        keywords = nlp.get("keywords", [])[:5]
        if keywords:
            console.print(
                f"  • Top keywords: {', '.join([kw['keyword'] for kw in keywords])}"
            )

    # Display trading analysis
    trading = result.get("trading", {})
    if trading and trading.get("is_trading_content"):
        console.print("\n[bold]Trading Analysis:[/bold]")
        console.print(f"  • Relevance Score: {trading.get('relevance_score', 0):.2f}")

        if trading.get("indicators"):
            indicators = [ind["concept"] for ind in trading["indicators"][:5]]
            console.print(f"  • Indicators: {', '.join(indicators)}")

        if trading.get("strategies"):
            strategies = [s["concept"] for s in trading["strategies"][:3]]
            console.print(f"  • Strategies: {', '.join(strategies)}")

    # Display chunks info
    chunks = result.get("chunks", [])
    if chunks:
        console.print(f"\n[bold]Created {len(chunks)} chunks[/bold]")


def _save_to_database(result: dict):
    """Save transcript to database"""
    try:
        from database.database import SessionLocal
        from database.models import Transcript, Chunk, Tag
        from datetime import datetime

        console.print("\n[yellow]Saving to database...[/yellow]")

        db = SessionLocal()

        metadata = result.get("metadata", {})

        # Create transcript record
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

        # Add tags from NLP
        nlp = result.get("nlp", {})
        for entity in nlp.get("entities", [])[:50]:  # Limit to top 50
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
        db.close()

        console.print("[green]Saved to database successfully![/green]")

    except Exception as e:
        console.print(f"[red]Error saving to database: {e}[/red]")


def _save_to_file(result: dict, output: str, format: str):
    """Save transcript to file"""
    try:
        console.print(f"\n[yellow]Saving to file: {output}...[/yellow]")

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            with open(output_path, "w") as f:
                json.dump(result, f, indent=2, default=str)

        elif format == "txt":
            with open(output_path, "w") as f:
                f.write(result.get("full_text", ""))

        elif format == "srt":
            _save_as_srt(result, output_path)

        console.print(f"[green]Saved to: {output_path}[/green]")

    except Exception as e:
        console.print(f"[red]Error saving file: {e}[/red]")


def _save_as_srt(result: dict, output_path: Path):
    """Save transcript in SRT subtitle format"""
    from datetime import timedelta

    with open(output_path, "w") as f:
        for i, segment in enumerate(result.get("transcript", []), 1):
            start = timedelta(seconds=segment.get("start", 0))
            end = timedelta(seconds=segment.get("end", 0))

            # Format: HH:MM:SS,mmm
            start_str = f"{int(start.seconds // 3600):02d}:{int((start.seconds % 3600) // 60):02d}:{int(start.seconds % 60):02d},{int(start.microseconds / 1000):03d}"
            end_str = f"{int(end.seconds // 3600):02d}:{int((end.seconds % 3600) // 60):02d}:{int(end.seconds % 60):02d},{int(end.microseconds / 1000):03d}"

            f.write(f"{i}\n")
            f.write(f"{start_str} --> {end_str}\n")
            f.write(f"{segment.get('text', '')}\n\n")
