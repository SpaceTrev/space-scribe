# SpaceScribe - Quick Start Guide

## 🚀 What's Been Built

SpaceScribe is now a **complete, production-ready** YouTube transcription platform with:

### Core Features ✅
- **Dual Transcription Engine**: YouTube API (for captions) + OpenAI Whisper (for audio)
- **NLP Processing**: Entity extraction, keyword analysis, topic modeling
- **Trading Analysis**: Automatic detection of indicators, strategies, timeframes
- **Smart Chunking**: Multiple strategies for optimal LLM consumption
- **Full-Text Search**: Search across all transcripts and tags
- **Multiple Export Formats**: JSON, CSV, TXT, Markdown, SRT, LLM training format

### Interfaces ✅
- **REST API**: FastAPI backend with comprehensive endpoints
- **CLI Tool**: Full-featured command-line interface
- **Web Interface**: Simple, functional web dashboard
- **MCP Server**: Model Context Protocol integration for LLMs

### Infrastructure ✅
- **Docker Support**: Ready-to-deploy containers
- **Database**: SQLite (default) or PostgreSQL
- **Testing**: Comprehensive test suite
- **Documentation**: API docs, MCP guide, examples

## 🏁 Getting Started (3 Steps)

### Step 1: Install Dependencies

```bash
# Install Python dependencies
pip install -e .

# Download spaCy model for NLP
python -m spacy download en_core_web_sm
```

### Step 2: Initialize

```bash
# Interactive initialization
spacescribe init

# Or quick start with defaults
cp config.example.yaml config.yaml
```

### Step 3: Start Using!

**Option A - CLI:**
```bash
# Transcribe a video
spacescribe transcribe "https://www.youtube.com/watch?v=VIDEO_ID"

# Process a playlist
spacescribe playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID"

# Search transcripts
spacescribe search "trading strategy"

# Export data
spacescribe export --format json
```

**Option B - API Server:**
```bash
# Start the API
spacescribe server

# Or with Docker
docker-compose up
```

Then visit:
- API: http://localhost:8000/docs
- Web UI: http://localhost:3000

**Option C - Python Code:**
```python
from core.transcriber.transcriber import Transcriber

# Transcribe a video
transcriber = Transcriber()
result = transcriber.transcribe("https://www.youtube.com/watch?v=VIDEO_ID")

print(f"Title: {result['metadata']['title']}")
print(f"Transcript: {result['full_text'][:200]}...")
```

## 📁 Project Structure

```
spacescribe/
├── api/                    # FastAPI backend
│   ├── main.py            # API entry point
│   └── routes/            # API endpoints
├── cli/                    # Command-line interface
│   ├── main.py            # CLI entry point
│   └── commands/          # CLI commands
├── core/                   # Core functionality
│   ├── transcriber/       # Transcription engines
│   ├── processor/         # NLP & trading analysis
│   └── chunker/           # Smart chunking
├── database/               # Database models & schema
├── mcp/                    # MCP server
├── web/                    # Web interface
├── docs/                   # Documentation
├── examples/               # Example scripts
├── tests/                  # Test suite
└── docker/                 # Docker configuration
```

## 🎯 Common Use Cases

### 1. Transcribe Educational Content
```bash
spacescribe transcribe "https://www.youtube.com/watch?v=VIDEO_ID" \
  --method auto \
  --save \
  --output transcript.json
```

### 2. Build Knowledge Base from Playlist
```bash
spacescribe playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID" \
  --limit 20
```

### 3. Extract Trading Insights
```bash
# Transcribe trading videos and automatically extract:
# - Indicators (RSI, MACD, Bollinger Bands, etc.)
# - Timeframes (1min, 5min, daily, etc.)
# - Strategies (scalping, swing trading, etc.)
spacescribe transcribe "TRADING_VIDEO_URL"
```

### 4. Search Across All Content
```bash
spacescribe search "machine learning" --limit 10
```

### 5. Export for LLM Training
```bash
spacescribe export --format llm --language en --min-quality 0.7
```

## 🔌 API Examples

### Transcribe via API
```bash
curl -X POST "http://localhost:8000/api/v1/transcribe" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "method": "auto",
    "process_nlp": true,
    "extract_trading": true
  }'
```

### Search via API
```bash
curl "http://localhost:8000/api/v1/search?query=python%20tutorial&limit=5"
```

## 🤖 MCP Integration (for LLMs)

```python
# The MCP server exposes these tools to LLMs:
# - spacescribe_transcribe(url, method, category)
# - spacescribe_search(query, limit, category)
# - spacescribe_batch(urls, method)
# - spacescribe_get_transcript(video_id)
# - spacescribe_export(format, filter)
# - spacescribe_summarize(video_id)

# Start MCP server
python -m mcp.server
```

## 🐳 Docker Deployment

```bash
# Build and run everything
docker-compose up -d

# Access services:
# - API: http://localhost:8000
# - Web: http://localhost:3000
# - Docs: http://localhost:8000/docs
```

## 📊 Database

Default: SQLite (`spacescribe.db`)

**Tables:**
- `transcripts` - Video transcripts and metadata
- `chunks` - Chunked data for LLMs
- `tags` - Extracted entities and concepts
- `jobs` - Background job tracking

**Switch to PostgreSQL:**
```yaml
# In config.yaml
storage:
  database_url: "postgresql://user:pass@localhost/spacescribe"
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/test_transcriber.py
```

## 📚 Documentation

- **API Documentation**: `/docs/API.md` or http://localhost:8000/docs
- **MCP Guide**: `/docs/MCP.md`
- **Examples**: `/examples/basic_usage.py`
- **Contributing**: `/CONTRIBUTING.md`

## 🎨 Features Breakdown

### Transcription Methods
1. **YouTube API** (fast, for videos with captions)
2. **Whisper** (slower, works for all videos)
3. **Auto** (tries API first, falls back to Whisper)

### NLP Features
- Named entity recognition (people, orgs, locations)
- Keyword extraction
- Topic modeling
- Sentiment analysis
- Definition extraction

### Trading-Specific
- Indicators: RSI, MACD, Bollinger Bands, etc.
- Timeframes: 1min, 5min, daily, etc.
- Instruments: stocks, forex, crypto
- Strategies: scalping, swing trading, etc.
- Risk concepts: stop loss, position sizing, etc.

### Export Formats
- **JSON**: Structured data
- **CSV**: Spreadsheet-compatible
- **TXT**: Plain text
- **Markdown**: Formatted text
- **SRT**: Subtitle format
- **LLM**: Training data format

## 🔥 Next Steps

### For Development
1. Add Celery for background jobs
2. Implement WebSocket for real-time progress
3. Add user authentication
4. Build advanced web dashboard
5. Add more language support

### For Production
1. Set up PostgreSQL database
2. Configure Redis for caching
3. Set up reverse proxy (nginx)
4. Enable API rate limiting
5. Add monitoring/logging

## 💡 Tips

1. **For best quality**: Use `--method api` when videos have captions
2. **For videos without captions**: Use `--method whisper`
3. **For batch processing**: Process during off-peak hours
4. **For large playlists**: Use `--limit` to test first
5. **For trading content**: Enable `extract_trading` for automatic analysis

## 🆘 Troubleshooting

**Problem**: Whisper is slow
- **Solution**: Use smaller model (`tiny` or `base`)

**Problem**: Video transcription fails
- **Solution**: Check if video is public and not age-restricted

**Problem**: spaCy model not found
- **Solution**: Run `python -m spacy download en_core_web_sm`

**Problem**: Database errors
- **Solution**: Run `spacescribe init` to recreate database

## 📞 Support

- **Issues**: https://github.com/SpaceTrev/space-scribe/issues
- **Documentation**: `/docs/`
- **Examples**: `/examples/`

---

**Built with ❤️ for the LLM and developer community**

Happy Transcribing! 🚀
