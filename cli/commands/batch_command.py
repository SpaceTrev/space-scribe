"""Batch transcribe command"""
from rich.console import Console
from rich.progress import Progress, TaskID
from typing import List, Optional
import concurrent.futures

console = Console()


def run(urls: List[str], method: Optional[str], parallel: int):
    """
    Batch transcribe multiple videos

    Args:
        urls: List of YouTube URLs
        method: Transcription method
        parallel: Number of parallel workers
    """
    from core.transcriber.transcriber import Transcriber

    console.print(f"\n[bold cyan]Batch transcribing {len(urls)} videos[/bold cyan]\n")

    transcriber = Transcriber(default_method=method or "auto")
    results = []

    if parallel > 1:
        # Parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {
                executor.submit(transcriber.transcribe, url): url for url in urls
            }

            with Progress() as progress:
                task = progress.add_task(
                    "[cyan]Transcribing videos...", total=len(urls)
                )

                for future in concurrent.futures.as_completed(futures):
                    url = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                        status = "✓" if result.get("success") else "✗"
                        console.print(f"{status} {url}")
                    except Exception as e:
                        console.print(f"✗ {url} - Error: {e}")
                    progress.update(task, advance=1)
    else:
        # Sequential processing
        with Progress() as progress:
            task = progress.add_task("[cyan]Transcribing videos...", total=len(urls))

            for url in urls:
                try:
                    result = transcriber.transcribe(url)
                    results.append(result)
                    status = "✓" if result.get("success") else "✗"
                    console.print(f"{status} {url}")
                except Exception as e:
                    console.print(f"✗ {url} - Error: {e}")
                progress.update(task, advance=1)

    # Summary
    successful = sum(1 for r in results if r.get("success"))
    failed = len(results) - successful

    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  • Total: {len(urls)}")
    console.print(f"  • Successful: [green]{successful}[/green]")
    console.print(f"  • Failed: [red]{failed}[/red]")
