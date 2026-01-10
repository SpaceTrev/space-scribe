"""SpaceScribe CLI - Main entry point"""
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
import yaml
from pathlib import Path
import sys
from typing import Optional, List
import logging

# Import CLI modules
from cli.commands import (
    init_command,
    transcribe_command,
    batch_command,
    playlist_command,
    search_command,
    export_command,
    list_command,
    delete_command,
    stats_command,
    server_command,
)

# Create Typer app
app = typer.Typer(
    name="spacescribe",
    help="SpaceScribe - Comprehensive YouTube video transcription platform",
    add_completion=False,
)

console = Console()


# Global options
@app.callback()
def main(
    ctx: typer.Context,
    config: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
):
    """SpaceScribe - YouTube video transcription platform"""
    # Set up logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Store config path in context
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["verbose"] = verbose


# Commands
@app.command()
def init(
    config_path: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to save config file",
    ),
):
    """Initialize SpaceScribe configuration"""
    init_command.run(config_path)


@app.command()
def transcribe(
    url: str = typer.Argument(..., help="YouTube video URL or ID"),
    method: Optional[str] = typer.Option(
        None,
        "--method",
        "-m",
        help="Transcription method: auto, api, or whisper",
    ),
    language: Optional[str] = typer.Option(
        None,
        "--language",
        "-l",
        help="Language code (e.g., 'en', 'es')",
    ),
    save: bool = typer.Option(
        True,
        "--save/--no-save",
        help="Save to database",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path",
    ),
    format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json, txt, srt",
    ),
):
    """Transcribe a single YouTube video"""
    transcribe_command.run(url, method, language, save, output, format)


@app.command()
def batch(
    urls: List[str] = typer.Argument(..., help="YouTube video URLs"),
    method: Optional[str] = typer.Option(
        None,
        "--method",
        "-m",
        help="Transcription method: auto, api, or whisper",
    ),
    parallel: int = typer.Option(
        1,
        "--parallel",
        "-p",
        help="Number of parallel transcriptions",
    ),
):
    """Batch transcribe multiple videos"""
    batch_command.run(urls, method, parallel)


@app.command()
def playlist(
    url: str = typer.Argument(..., help="YouTube playlist URL"),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of videos to process",
    ),
    method: Optional[str] = typer.Option(
        None,
        "--method",
        "-m",
        help="Transcription method: auto, api, or whisper",
    ),
):
    """Process entire YouTube playlist"""
    playlist_command.run(url, limit, method)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum results to return",
    ),
    category: Optional[str] = typer.Option(
        None,
        "--category",
        "-c",
        help="Filter by category",
    ),
):
    """Search transcripts"""
    search_command.run(query, limit, category)


@app.command()
def export(
    format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Export format: json, csv, txt, markdown, srt, llm",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path",
    ),
    filter: Optional[str] = typer.Option(
        None,
        "--filter",
        help="Filter expression (e.g., 'language=en')",
    ),
):
    """Export transcripts in various formats"""
    export_command.run(format, output, filter)


@app.command()
def list(
    category: Optional[str] = typer.Option(
        None,
        "--category",
        "-c",
        help="Filter by category tag",
    ),
    limit: int = typer.Option(
        20,
        "--limit",
        "-l",
        help="Maximum results to display",
    ),
    sort: str = typer.Option(
        "created_at",
        "--sort",
        "-s",
        help="Sort by: created_at, title, duration",
    ),
):
    """List all transcripts"""
    list_command.run(category, limit, sort)


@app.command()
def delete(
    video_id: str = typer.Argument(..., help="Video ID to delete"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation",
    ),
):
    """Delete a transcript"""
    delete_command.run(video_id, force)


@app.command()
def stats():
    """Show database statistics"""
    stats_command.run()


@app.command()
def server(
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        "-h",
        help="Server host",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Server port",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        help="Enable auto-reload",
    ),
):
    """Start the API server"""
    server_command.run(host, port, reload)


# Version command
@app.command()
def version():
    """Show SpaceScribe version"""
    from rich.panel import Panel

    version_info = """
    [bold cyan]SpaceScribe[/bold cyan] v0.1.0

    A comprehensive YouTube transcription platform

    GitHub: https://github.com/SpaceTrev/space-scribe
    """

    console.print(Panel(version_info, title="Version", border_style="cyan"))


if __name__ == "__main__":
    app()
