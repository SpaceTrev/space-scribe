"""Server command"""
from rich.console import Console

console = Console()


def run(host: str, port: int, reload: bool):
    """
    Start the API server

    Args:
        host: Server host
        port: Server port
        reload: Enable auto-reload
    """
    import uvicorn

    console.print(f"\n[bold cyan]Starting SpaceScribe API server[/bold cyan]\n")
    console.print(f"  • Host: {host}")
    console.print(f"  • Port: {port}")
    console.print(f"  • Reload: {reload}\n")
    console.print(f"[green]Server will be available at: http://{host}:{port}[/green]")
    console.print(f"[green]API docs: http://{host}:{port}/docs[/green]\n")

    try:
        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]\n")
    except Exception as e:
        console.print(f"\n[red]Error starting server: {e}[/red]\n")
