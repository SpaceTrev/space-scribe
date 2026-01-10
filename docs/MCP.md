# SpaceScribe MCP Integration

## Overview

SpaceScribe provides a Model Context Protocol (MCP) server that exposes transcription functionality to LLMs like Claude.

## Installation

```bash
# Python package
pip install spacescribe

# Or install from source
git clone https://github.com/SpaceTrev/space-scribe.git
cd space-scribe
pip install -e .
```

## Running the MCP Server

```bash
# Start MCP server in stdio mode
python -m mcp.server
```

## Available Tools

### 1. spacescribe_transcribe

Transcribe a YouTube video and return the full transcript with metadata.

**Parameters:**
- `url` (required): YouTube video URL or ID
- `method` (optional): Transcription method (`auto`, `api`, or `whisper`)
- `category` (optional): Category tag for the transcript

**Example:**
```json
{
  "tool": "spacescribe_transcribe",
  "parameters": {
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "method": "auto",
    "category": "trading"
  }
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "video_id": "VIDEO_ID",
    "title": "Video Title",
    "channel": "Channel Name",
    "transcript": "Full transcript text...",
    "summary": ["Key sentence 1", "Key sentence 2"],
    "keywords": ["keyword1", "keyword2"],
    "entities": ["entity1", "entity2"]
  }
}
```

### 2. spacescribe_search

Search across all transcripts for specific content.

**Parameters:**
- `query` (required): Search query text
- `limit` (optional): Maximum results (default: 10)
- `category` (optional): Filter by category tag

**Example:**
```json
{
  "tool": "spacescribe_search",
  "parameters": {
    "query": "trading strategies",
    "limit": 5
  }
}
```

### 3. spacescribe_batch

Transcribe multiple YouTube videos in batch.

**Parameters:**
- `urls` (required): Array of YouTube video URLs
- `method` (optional): Transcription method

**Example:**
```json
{
  "tool": "spacescribe_batch",
  "parameters": {
    "urls": [
      "https://www.youtube.com/watch?v=VIDEO_ID_1",
      "https://www.youtube.com/watch?v=VIDEO_ID_2"
    ]
  }
}
```

### 4. spacescribe_get_transcript

Get a previously transcribed video by video ID.

**Parameters:**
- `video_id` (required): YouTube video ID

**Example:**
```json
{
  "tool": "spacescribe_get_transcript",
  "parameters": {
    "video_id": "VIDEO_ID"
  }
}
```

### 5. spacescribe_export

Export transcripts in various formats.

**Parameters:**
- `format` (optional): Export format (`json`, `csv`, `txt`, `markdown`, `llm`)
- `filter` (optional): Filter criteria object

**Example:**
```json
{
  "tool": "spacescribe_export",
  "parameters": {
    "format": "json",
    "filter": {
      "language": "en",
      "min_quality": 0.7
    }
  }
}
```

### 6. spacescribe_summarize

Get a summary of a transcript using NLP analysis.

**Parameters:**
- `video_id` (required): YouTube video ID

**Example:**
```json
{
  "tool": "spacescribe_summarize",
  "parameters": {
    "video_id": "VIDEO_ID"
  }
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "video_id": "VIDEO_ID",
    "title": "Video Title",
    "summary_sentences": ["Sentence 1", "Sentence 2"],
    "keywords": ["keyword1", "keyword2"],
    "topics": ["topic1", "topic2"],
    "entities": [
      {"text": "Entity Name", "type": "PERSON"}
    ],
    "statistics": {
      "total_tokens": 5000,
      "total_sentences": 120,
      "unique_entities": 15
    }
  }
}
```

## Claude Desktop Integration

To use SpaceScribe with Claude Desktop, add this to your Claude config:

```json
{
  "mcpServers": {
    "spacescribe": {
      "command": "python",
      "args": ["-m", "mcp.server"],
      "cwd": "/path/to/space-scribe"
    }
  }
}
```

## Example Usage with Claude

```
Human: Can you transcribe this YouTube video for me? https://www.youtube.com/watch?v=VIDEO_ID

Claude: I'll use SpaceScribe to transcribe that video for you.
[Calls spacescribe_transcribe tool]

Here's what I found:
- Video: "Title of the Video"
- Channel: Channel Name
- Duration: 10 minutes
- Language: English

The video discusses [summary based on transcript]...

Key points:
1. [Point from transcript]
2. [Point from transcript]
3. [Point from transcript]

Would you like me to search for similar content or export this transcript?
```

## Error Handling

The MCP server includes automatic retry logic for failed requests and proper error messages:

```json
{
  "success": false,
  "error": "Transcription failed: Video unavailable"
}
```

## Caching

Frequently accessed transcripts are cached automatically to improve performance.

## Best Practices

1. **Check if already transcribed**: Use `spacescribe_get_transcript` before transcribing to avoid duplicates
2. **Use appropriate methods**: Use `api` for videos with captions, `whisper` for those without
3. **Batch operations**: Use `spacescribe_batch` for multiple videos to improve efficiency
4. **Export regularly**: Use `spacescribe_export` to backup your transcripts

## Troubleshooting

### MCP server won't start
- Check that SpaceScribe is installed: `pip list | grep spacescribe`
- Verify database is initialized: `spacescribe init`
- Check logs for errors

### Transcription fails
- Verify the video URL is correct and accessible
- Check if the video has captions (for `api` method)
- Try different transcription method
- Check network connectivity

### Slow performance
- Whisper transcription is slower than API method
- Consider using smaller Whisper model for faster results
- Check system resources (CPU/GPU usage)
