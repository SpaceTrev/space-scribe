# SpaceScribe API Documentation

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, SpaceScribe uses API key authentication (optional). Include your API key in the header:

```
X-API-Key: your-api-key
```

## Endpoints

### Health Check

#### GET /health

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "SpaceScribe API",
  "version": "0.1.0"
}
```

### Transcription

#### POST /transcribe

Transcribe a single YouTube video.

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "method": "auto",
  "language": "en",
  "save_to_db": true,
  "process_nlp": true,
  "extract_trading": true
}
```

**Parameters:**
- `url` (required): YouTube video URL or ID
- `method` (optional): `auto`, `api`, or `whisper` (default: `auto`)
- `language` (optional): Language code (e.g., `en`, `es`)
- `save_to_db` (optional): Save to database (default: `true`)
- `process_nlp` (optional): Run NLP processing (default: `true`)
- `extract_trading` (optional): Extract trading concepts (default: `true`)

**Response:**
```json
{
  "success": true,
  "video_id": "VIDEO_ID",
  "method": "api",
  "language": "en",
  "quality_score": 0.85,
  "transcript_length": 15420,
  "chunks_count": 15,
  "message": "Transcription completed successfully"
}
```

#### POST /batch

Batch transcribe multiple videos.

**Request Body:**
```json
{
  "urls": [
    "https://www.youtube.com/watch?v=VIDEO_ID_1",
    "https://www.youtube.com/watch?v=VIDEO_ID_2"
  ],
  "method": "auto",
  "parallel": 1
}
```

**Response:**
```json
{
  "total": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "url": "...",
      "success": true,
      "video_id": "VIDEO_ID_1"
    }
  ]
}
```

#### GET /transcripts

List all transcripts with pagination and filters.

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum results (default: 20)
- `language` (optional): Filter by language
- `method` (optional): Filter by transcription method

**Response:**
```json
{
  "total": 50,
  "skip": 0,
  "limit": 20,
  "transcripts": [
    {
      "video_id": "VIDEO_ID",
      "title": "Video Title",
      "channel_name": "Channel Name",
      "duration_seconds": 600,
      "language": "en",
      "method": "api",
      "quality_score": 0.85,
      "created_at": "2024-01-10T12:00:00"
    }
  ]
}
```

#### GET /transcripts/{video_id}

Get a specific transcript.

**Response:**
```json
{
  "video_id": "VIDEO_ID",
  "title": "Video Title",
  "channel_name": "Channel Name",
  "youtube_url": "https://...",
  "duration_seconds": 600,
  "language": "en",
  "method": "api",
  "quality_score": 0.85,
  "transcript": "Full transcript text...",
  "created_at": "2024-01-10T12:00:00"
}
```

#### DELETE /transcripts/{video_id}

Delete a transcript.

**Response:**
```json
{
  "success": true,
  "message": "Transcript VIDEO_ID deleted"
}
```

### Search

#### GET /search

Full-text search across transcripts.

**Query Parameters:**
- `query` (required): Search query text
- `limit` (optional): Maximum results (default: 10)
- `category` (optional): Filter by tag category
- `language` (optional): Filter by language
- `min_quality` (optional): Minimum quality score

**Response:**
```json
{
  "query": "trading strategy",
  "total_results": 5,
  "results": [
    {
      "video_id": "VIDEO_ID",
      "title": "Video Title",
      "channel_name": "Channel Name",
      "youtube_url": "https://...",
      "transcript_preview": "Preview text...",
      "created_at": "2024-01-10T12:00:00"
    }
  ]
}
```

#### GET /search/tags

Search by tags.

**Query Parameters:**
- `tags` (required): Comma-separated tag names
- `match_all` (optional): Match all tags (default: false)
- `limit` (optional): Maximum results (default: 10)

**Response:**
```json
{
  "tags": ["RSI", "MACD"],
  "match_all": false,
  "total_results": 3,
  "results": [...]
}
```

### Export

#### GET /export

Export transcripts in various formats.

**Query Parameters:**
- `format` (optional): Export format - `json`, `csv`, `txt`, `markdown`, `llm` (default: `json`)
- `language` (optional): Filter by language
- `method` (optional): Filter by method
- `min_quality` (optional): Minimum quality score
- `limit` (optional): Maximum transcripts to export

**Response:**
Depends on format. For JSON:
```json
[
  {
    "video_id": "VIDEO_ID",
    "title": "Video Title",
    "transcript": "Full text..."
  }
]
```

#### GET /export/{video_id}

Export a single transcript.

**Query Parameters:**
- `format` (optional): Export format (default: `json`)
- `include_chunks` (optional): Include chunks (default: true)
- `include_tags` (optional): Include tags (default: true)

**Response:**
```json
{
  "video_id": "VIDEO_ID",
  "title": "Video Title",
  "transcript": "...",
  "chunks": [...],
  "tags": [...]
}
```

## Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Error message"
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Rate Limiting

Currently no rate limiting is enforced. Configure in production settings.

## Examples

### cURL Examples

**Transcribe a video:**
```bash
curl -X POST "http://localhost:8000/api/v1/transcribe" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "method": "auto"
  }'
```

**Search transcripts:**
```bash
curl "http://localhost:8000/api/v1/search?query=trading&limit=5"
```

**Export as JSON:**
```bash
curl "http://localhost:8000/api/v1/export?format=json&limit=10"
```

### Python Example

```python
import requests

# Transcribe video
response = requests.post(
    "http://localhost:8000/api/v1/transcribe",
    json={
        "url": "https://www.youtube.com/watch?v=VIDEO_ID",
        "method": "auto"
    }
)
result = response.json()
print(f"Transcribed: {result['video_id']}")

# Search
response = requests.get(
    "http://localhost:8000/api/v1/search",
    params={"query": "trading strategy", "limit": 10}
)
results = response.json()
print(f"Found {results['total_results']} results")
```
