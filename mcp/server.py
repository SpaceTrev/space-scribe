"""MCP Server for SpaceScribe

This server exposes SpaceScribe functionality to LLMs via the Model Context Protocol.
"""
import json
import logging
from typing import Any, Dict, List, Optional
import sys

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP Server implementation for SpaceScribe"""

    def __init__(self):
        """Initialize MCP server"""
        self.tools = self._register_tools()
        logger.info("MCP Server initialized with tools: " + ", ".join(self.tools.keys()))

    def _register_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register available tools"""
        return {
            "spacescribe_transcribe": {
                "description": "Transcribe a YouTube video and return the full transcript with metadata",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "YouTube video URL or ID",
                        },
                        "method": {
                            "type": "string",
                            "enum": ["auto", "api", "whisper"],
                            "description": "Transcription method to use",
                            "default": "auto",
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional category tag for the transcript",
                        },
                    },
                    "required": ["url"],
                },
                "handler": self._handle_transcribe,
            },
            "spacescribe_search": {
                "description": "Search across all transcripts for specific content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query text",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10,
                        },
                        "category": {
                            "type": "string",
                            "description": "Filter by category tag",
                        },
                    },
                    "required": ["query"],
                },
                "handler": self._handle_search,
            },
            "spacescribe_batch": {
                "description": "Transcribe multiple YouTube videos in batch",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "urls": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of YouTube video URLs",
                        },
                        "method": {
                            "type": "string",
                            "enum": ["auto", "api", "whisper"],
                            "default": "auto",
                        },
                    },
                    "required": ["urls"],
                },
                "handler": self._handle_batch,
            },
            "spacescribe_get_transcript": {
                "description": "Get a previously transcribed video by video ID",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "YouTube video ID",
                        },
                    },
                    "required": ["video_id"],
                },
                "handler": self._handle_get_transcript,
            },
            "spacescribe_export": {
                "description": "Export transcripts in various formats",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "enum": ["json", "csv", "txt", "markdown", "llm"],
                            "description": "Export format",
                            "default": "json",
                        },
                        "filter": {
                            "type": "object",
                            "description": "Filter criteria (language, method, min_quality)",
                        },
                    },
                },
                "handler": self._handle_export,
            },
            "spacescribe_summarize": {
                "description": "Get a summary of a transcript using NLP analysis",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "YouTube video ID",
                        },
                    },
                    "required": ["video_id"],
                },
                "handler": self._handle_summarize,
            },
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        return [
            {
                "name": name,
                "description": tool["description"],
                "parameters": tool["parameters"],
            }
            for name, tool in self.tools.items()
        ]

    def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool with parameters

        Args:
            tool_name: Name of the tool to call
            parameters: Tool parameters

        Returns:
            Tool result
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(self.tools.keys()),
            }

        try:
            handler = self.tools[tool_name]["handler"]
            result = handler(parameters)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _handle_transcribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle transcribe tool"""
        from core.transcriber.transcriber import Transcriber
        from core.processor.nlp_processor import NLPProcessor
        from database.database import SessionLocal
        from database.models import Transcript

        url = params.get("url")
        method = params.get("method", "auto")
        category = params.get("category")

        # Check if already transcribed
        db = SessionLocal()
        from core.transcriber.youtube_transcriber import YouTubeTranscriber

        yt = YouTubeTranscriber()
        video_id = yt.extract_video_id(url)

        if video_id:
            existing = (
                db.query(Transcript).filter(Transcript.video_id == video_id).first()
            )
            if existing:
                db.close()
                return {
                    "cached": True,
                    "video_id": existing.video_id,
                    "title": existing.title,
                    "transcript": existing.transcript_full,
                    "language": existing.language,
                }

        db.close()

        # Transcribe
        transcriber = Transcriber(default_method=method)
        result = transcriber.transcribe(url, method=method)

        if not result.get("success"):
            return {
                "error": result.get("message", "Transcription failed"),
                "details": result,
            }

        # Process with NLP
        nlp_processor = NLPProcessor()
        nlp_result = nlp_processor.process_transcript(result["full_text"])

        return {
            "video_id": result["video_id"],
            "title": result["metadata"].get("title"),
            "channel": result["metadata"].get("channel_name"),
            "duration": result["metadata"].get("duration_seconds"),
            "language": result["language"],
            "method": result["method"],
            "transcript": result["full_text"],
            "quality_score": result.get("quality_score"),
            "summary": nlp_result.get("summary_sentences", []),
            "keywords": [kw["keyword"] for kw in nlp_result.get("keywords", [])[:10]],
            "entities": [ent["text"] for ent in nlp_result.get("entities", [])[:10]],
        }

    def _handle_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search tool"""
        from database.database import SessionLocal
        from database.models import Transcript, Tag
        from sqlalchemy import or_

        query = params.get("query")
        limit = params.get("limit", 10)
        category = params.get("category")

        db = SessionLocal()

        # Build query
        search_query = db.query(Transcript).filter(
            or_(
                Transcript.transcript_full.contains(query),
                Transcript.title.contains(query),
                Transcript.channel_name.contains(query),
            )
        )

        if category:
            search_query = (
                search_query.join(Tag)
                .filter(Tag.tag_category == category)
                .distinct()
            )

        results = search_query.limit(limit).all()

        db.close()

        return {
            "query": query,
            "total_results": len(results),
            "results": [
                {
                    "video_id": t.video_id,
                    "title": t.title,
                    "channel": t.channel_name,
                    "url": t.youtube_url,
                    "transcript_preview": (
                        t.transcript_full[:300] + "..."
                        if len(t.transcript_full or "") > 300
                        else t.transcript_full
                    ),
                }
                for t in results
            ],
        }

    def _handle_batch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle batch transcribe tool"""
        from core.transcriber.transcriber import Transcriber

        urls = params.get("urls", [])
        method = params.get("method", "auto")

        transcriber = Transcriber(default_method=method)
        results = []

        for url in urls:
            try:
                result = transcriber.transcribe(url, method=method)
                results.append(
                    {
                        "url": url,
                        "success": result.get("success", False),
                        "video_id": result.get("video_id"),
                        "title": result.get("metadata", {}).get("title"),
                    }
                )
            except Exception as e:
                results.append({"url": url, "success": False, "error": str(e)})

        successful = sum(1 for r in results if r.get("success"))

        return {
            "total": len(urls),
            "successful": successful,
            "failed": len(urls) - successful,
            "results": results,
        }

    def _handle_get_transcript(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get transcript tool"""
        from database.database import SessionLocal
        from database.models import Transcript

        video_id = params.get("video_id")

        db = SessionLocal()
        transcript = (
            db.query(Transcript).filter(Transcript.video_id == video_id).first()
        )

        if not transcript:
            db.close()
            return {"error": f"Transcript not found for video ID: {video_id}"}

        result = {
            "video_id": transcript.video_id,
            "title": transcript.title,
            "channel": transcript.channel_name,
            "url": transcript.youtube_url,
            "language": transcript.language,
            "transcript": transcript.transcript_full,
            "duration": transcript.duration_seconds,
            "method": transcript.transcript_method,
            "quality_score": transcript.quality_score,
        }

        db.close()
        return result

    def _handle_export(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle export tool"""
        from database.database import SessionLocal
        from database.models import Transcript

        format_type = params.get("format", "json")
        filter_criteria = params.get("filter", {})

        db = SessionLocal()
        query = db.query(Transcript)

        # Apply filters
        if "language" in filter_criteria:
            query = query.filter(Transcript.language == filter_criteria["language"])
        if "method" in filter_criteria:
            query = query.filter(
                Transcript.transcript_method == filter_criteria["method"]
            )
        if "min_quality" in filter_criteria:
            query = query.filter(
                Transcript.quality_score >= filter_criteria["min_quality"]
            )

        transcripts = query.all()

        db.close()

        if not transcripts:
            return {"error": "No transcripts found matching criteria"}

        # Format based on type
        if format_type == "json":
            return {
                "format": "json",
                "count": len(transcripts),
                "transcripts": [
                    {
                        "video_id": t.video_id,
                        "title": t.title,
                        "transcript": t.transcript_full,
                    }
                    for t in transcripts
                ],
            }
        else:
            return {
                "format": format_type,
                "count": len(transcripts),
                "message": f"Export prepared in {format_type} format",
            }

    def _handle_summarize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle summarize tool"""
        from database.database import SessionLocal
        from database.models import Transcript
        from core.processor.nlp_processor import NLPProcessor

        video_id = params.get("video_id")

        db = SessionLocal()
        transcript = (
            db.query(Transcript).filter(Transcript.video_id == video_id).first()
        )

        if not transcript:
            db.close()
            return {"error": f"Transcript not found for video ID: {video_id}"}

        # Process with NLP
        nlp_processor = NLPProcessor()
        nlp_result = nlp_processor.process_transcript(transcript.transcript_full)

        db.close()

        return {
            "video_id": video_id,
            "title": transcript.title,
            "summary_sentences": nlp_result.get("summary_sentences", []),
            "keywords": [kw["keyword"] for kw in nlp_result.get("keywords", [])[:15]],
            "topics": [topic["topic"] for topic in nlp_result.get("topics", [])],
            "entities": [
                {"text": ent["text"], "type": ent["label"]}
                for ent in nlp_result.get("entities", [])[:20]
            ],
            "statistics": nlp_result.get("statistics", {}),
        }

    def run_stdio(self):
        """Run MCP server in stdio mode"""
        logger.info("Starting MCP server in stdio mode")

        while True:
            try:
                # Read request from stdin
                line = sys.stdin.readline()
                if not line:
                    break

                request = json.loads(line)

                if request.get("method") == "list_tools":
                    response = {"tools": self.list_tools()}
                elif request.get("method") == "call_tool":
                    tool_name = request.get("tool")
                    parameters = request.get("parameters", {})
                    response = self.call_tool(tool_name, parameters)
                else:
                    response = {"error": f"Unknown method: {request.get('method')}"}

                # Write response to stdout
                print(json.dumps(response))
                sys.stdout.flush()

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in MCP server: {e}", exc_info=True)
                print(json.dumps({"error": str(e)}))
                sys.stdout.flush()


def main():
    """Main entry point for MCP server"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    server = MCPServer()
    server.run_stdio()


if __name__ == "__main__":
    main()
