"""Initialize SpaceScribe configuration"""
from pathlib import Path
import yaml
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich import print as rprint

console = Console()


def run(config_path: str = None):
    """
    Initialize SpaceScribe configuration

    Args:
        config_path: Optional custom config path
    """
    console.print("\n[bold cyan]SpaceScribe Initialization[/bold cyan]\n")

    # Determine config path
    if config_path:
        config_file = Path(config_path)
    else:
        home_dir = Path.home()
        config_dir = home_dir / ".spacescribe"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "config.yaml"

    # Check if config already exists
    if config_file.exists():
        overwrite = Confirm.ask(
            f"Config file already exists at {config_file}. Overwrite?",
            default=False,
        )
        if not overwrite:
            console.print("[yellow]Initialization cancelled[/yellow]")
            return

    # Interactive configuration
    console.print("[bold]API Configuration[/bold]")
    api_key = Prompt.ask("API key (leave empty for none)", default="")
    base_url = Prompt.ask("API base URL", default="http://localhost:8000")

    console.print("\n[bold]Transcription Settings[/bold]")
    default_method = Prompt.ask(
        "Default transcription method",
        choices=["auto", "api", "whisper"],
        default="auto",
    )
    whisper_model = Prompt.ask(
        "Whisper model",
        choices=["tiny", "base", "small", "medium", "large"],
        default="base",
    )

    console.print("\n[bold]Database Settings[/bold]")
    use_postgres = Confirm.ask("Use PostgreSQL?", default=False)

    if use_postgres:
        db_user = Prompt.ask("Database user", default="postgres")
        db_password = Prompt.ask("Database password", password=True)
        db_host = Prompt.ask("Database host", default="localhost")
        db_name = Prompt.ask("Database name", default="spacescribe")
        database_url = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"
    else:
        database_url = "sqlite:///./spacescribe.db"

    # Create configuration
    config = {
        "api": {
            "base_url": base_url,
            "api_key": api_key if api_key else None,
            "timeout": 300,
            "host": "0.0.0.0",
            "port": 8000,
            "workers": 4,
        },
        "transcription": {
            "default_method": default_method,
            "whisper_model": whisper_model,
            "chunk_size": 1000,
            "overlap": 150,
            "languages": ["en"],
            "quality_threshold": 0.7,
        },
        "storage": {
            "database_url": database_url,
            "cache_enabled": True,
            "cache_ttl": 3600,
            "export_directory": "./exports",
            "temp_directory": "./temp",
        },
        "processing": {
            "max_concurrent_jobs": 5,
            "enable_nlp": True,
            "extract_entities": True,
            "auto_tag": True,
            "nlp_model": "en_core_web_sm",
            "batch_size": 10,
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "./logs/spacescribe.log",
            "max_size_mb": 100,
            "backup_count": 5,
        },
    }

    # Save configuration
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    console.print(f"\n[green]Configuration saved to: {config_file}[/green]")

    # Initialize database
    init_db = Confirm.ask("\nInitialize database now?", default=True)

    if init_db:
        try:
            from database.database import init_db as create_tables

            console.print("\n[yellow]Initializing database...[/yellow]")
            create_tables()
            console.print("[green]Database initialized successfully![/green]")
        except Exception as e:
            console.print(f"[red]Error initializing database: {e}[/red]")

    # Download spaCy model if needed
    if config["processing"]["enable_nlp"]:
        download_spacy = Confirm.ask(
            "\nDownload spaCy NLP model (required for NLP features)?",
            default=True,
        )

        if download_spacy:
            import subprocess

            try:
                console.print("\n[yellow]Downloading spaCy model...[/yellow]")
                subprocess.run(
                    ["python", "-m", "spacy", "download", "en_core_web_sm"],
                    check=True,
                )
                console.print("[green]spaCy model downloaded successfully![/green]")
            except Exception as e:
                console.print(f"[red]Error downloading spaCy model: {e}[/red]")
                console.print(
                    "[yellow]You can download it later with: python -m spacy download en_core_web_sm[/yellow]"
                )

    console.print("\n[bold green]SpaceScribe initialization complete![/bold green]")
    console.print("\nNext steps:")
    console.print("  1. Run: [cyan]spacescribe transcribe <youtube-url>[/cyan]")
    console.print("  2. Or start the server: [cyan]spacescribe server[/cyan]")
