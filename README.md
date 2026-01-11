# SpaceScribe 🚀📝

A comprehensive YouTube video transcription platform with web interface, API, CLI tools, and MCP integration. Convert YouTube videos into structured text data that any LLM can use for training, analysis, or knowledge extraction.

## Features

- **Multiple Transcription Methods**: YouTube API for videos with captions, Whisper for audio transcription
- **REST API**: Full-featured FastAPI backend with background job processing
- **CLI Tool**: Powerful command-line interface for batch operations
- **MCP Integration**: Model Context Protocol server for LLM integration
- **Web Interface**: Simple, functional dashboard for managing transcripts
- **NLP Processing**: Automatic entity extraction, tagging, and topic modeling
- **Smart Chunking**: Multiple strategies for optimal LLM consumption
- **Export Formats**: JSON, CSV, TXT, Markdown, SRT, and LLM training formats
- **Trading Analysis**: Specialized extraction for trading and market content

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/SpaceTrev/space-scribe.git
cd space-scribe

# Install dependencies
pip install -e .

# Download spaCy model
python -m spacy download en_core_web_sm

# Copy and configure settings
cp config.example.yaml config.yaml

# Initialize database
spacescribe init
```

### Basic Usage

**🌐 Web Interface (Easiest!)**
```bash
# Start the server
spacescribe server

# Open your browser to: http://localhost:8000
```
✨ The web interface provides a beautiful, easy-to-use dashboard where you can:
- Paste any YouTube URL and transcribe with one click
- View real-time transcription progress
- See transcript previews and metadata
- No command-line experience needed!

**💻 Command Line**
```bash
# Transcribe a single video
spacescribe transcribe "https://www.youtube.com/watch?v=VIDEO_ID"

# Process entire playlist
spacescribe playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID"

# Search transcripts
spacescribe search "trading strategy"

# Export all transcripts
spacescribe export --format json
```

**🔌 API Documentation**
```bash
# Start server and visit: http://localhost:8000/docs
spacescribe server
```

## Architecture

```
spacescribe/
├── api/              # FastAPI backend
├── cli/              # Command-line interface
├── core/             # Core transcription engine
├── mcp/              # MCP server integration
├── web/              # Web interface
├── database/         # Database models and migrations
├── tests/            # Test suite
└── docs/             # Documentation
```

## API Endpoints

- `POST /api/v1/transcribe` - Transcribe single video
- `POST /api/v1/batch` - Batch process multiple videos
- `GET /api/v1/transcripts/{video_id}` - Retrieve transcript
- `GET /api/v1/transcripts` - List all transcripts
- `GET /api/v1/search` - Full-text search
- `DELETE /api/v1/transcripts/{video_id}` - Remove transcript
- `GET /api/v1/export` - Export data
- `GET /api/v1/status/{job_id}` - Check job status

## CLI Commands

- `spacescribe init` - Initialize configuration
- `spacescribe transcribe <url>` - Transcribe single video
- `spacescribe batch <url1> <url2> ...` - Batch transcribe
- `spacescribe playlist <playlist-url>` - Process entire playlist
- `spacescribe search "query"` - Search transcripts
- `spacescribe export --format json|csv|txt` - Export data
- `spacescribe list [--category tag]` - List transcripts
- `spacescribe delete <video-id>` - Remove transcript
- `spacescribe stats` - Show statistics
- `spacescribe server` - Start local API server

## MCP Integration

Install the MCP server:

```bash
pip install spacescribe-mcp
```

Available tools for LLMs:
- `spacescribe_transcribe(url, category)`
- `spacescribe_search(query, limit)`
- `spacescribe_batch(urls)`
- `spacescribe_export(format, filter)`
- `spacescribe_get_transcript(video_id)`
- `spacescribe_summarize(video_id)`

## Configuration

Edit `config.yaml` to customize:

- Transcription methods and models
- Database connection
- API settings and rate limiting
- NLP processing options
- Export formats
- Chunking strategies

## Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up -d

# Access everything at http://localhost:8000
# - Web Interface: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - API: http://localhost:8000/api/v1
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .

# Type checking
mypy .
```

## Use Cases

1. **Educational Content**: Transcribe tutorials and create searchable knowledge bases
2. **Trading Analysis**: Extract strategies, indicators, and concepts from market videos
3. **Research**: Process playlists for academic or market research
4. **LLM Training**: Generate training data from YouTube content
5. **Accessibility**: Create transcripts and subtitles for videos

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## Support

- Issues: https://github.com/SpaceTrev/space-scribe/issues
- Documentation: https://spacescribe.io/docs
- Discord: https://discord.gg/spacescribe

---

Built with ❤️ for the LLM and developer community
