"""Playlist transcribe command"""
from rich.console import Console
from typing import Optional
import yt_dlp

console = Console()


def run(url: str, limit: Optional[int], method: Optional[str]):
    """
    Transcribe all videos in a playlist

    Args:
        url: Playlist URL
        limit: Maximum number of videos
        method: Transcription method
    """
    console.print(f"\n[bold cyan]Processing playlist:[/bold cyan] {url}\n")

    # Extract playlist videos
    try:
        ydl_opts = {
            "quiet": True,
            "extract_flat": True,
            "force_generic_extractor": False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            console.print("[yellow]Fetching playlist information...[/yellow]")
            info = ydl.extract_info(url, download=False)

            if "entries" not in info:
                console.print("[red]No videos found in playlist[/red]")
                return

            entries = info["entries"]

            if limit:
                entries = entries[:limit]

            console.print(
                f"[green]Found {len(entries)} videos[/green] (limit: {limit or 'none'})\n"
            )

            # Extract video URLs
            video_urls = []
            for entry in entries:
                if entry:
                    video_id = entry.get("id")
                    if video_id:
                        video_urls.append(f"https://www.youtube.com/watch?v={video_id}")

            if not video_urls:
                console.print("[red]No valid video URLs found[/red]")
                return

            # Use batch command to process
            from cli.commands.batch_command import run as batch_run

            batch_run(video_urls, method, parallel=1)

    except Exception as e:
        console.print(f"[red]Error processing playlist: {e}[/red]")
