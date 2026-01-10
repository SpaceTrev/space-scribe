"""Main transcriber that combines YouTube API and Whisper methods"""
import logging
from typing import Optional, Dict, Any, List
import yt_dlp
from datetime import datetime
from core.transcriber.youtube_transcriber import YouTubeTranscriber
from core.transcriber.whisper_transcriber import WhisperTranscriber

logger = logging.getLogger(__name__)


class Transcriber:
    """
    Main transcription class that intelligently chooses between
    YouTube API and Whisper based on availability and settings
    """

    def __init__(
        self,
        default_method: str = "auto",
        whisper_model: str = "base",
        languages: Optional[List[str]] = None,
    ):
        """
        Initialize transcriber

        Args:
            default_method: 'auto', 'api', or 'whisper'
            whisper_model: Whisper model size if using Whisper
            languages: Preferred languages for transcripts
        """
        self.default_method = default_method
        self.youtube_transcriber = YouTubeTranscriber(languages=languages)
        self.whisper_transcriber = WhisperTranscriber(model_name=whisper_model)

        logger.info(
            f"Initialized Transcriber with method: {default_method}, "
            f"Whisper model: {whisper_model}"
        )

    def transcribe(
        self,
        video_url: str,
        method: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe a YouTube video using the best available method

        Args:
            video_url: YouTube video URL or ID
            method: Override default method ('auto', 'api', or 'whisper')
            language: Preferred language code

        Returns:
            Comprehensive transcription result with metadata
        """
        chosen_method = method or self.default_method

        # Get video metadata first
        metadata = self.get_video_metadata(video_url)
        if not metadata:
            return {
                "success": False,
                "error": "metadata_failed",
                "message": "Could not fetch video metadata",
            }

        result = {
            "video_url": video_url,
            "video_id": metadata.get("id"),
            "metadata": metadata,
        }

        # Try to transcribe based on method
        if chosen_method == "whisper":
            # Force Whisper
            transcript_result = self._transcribe_with_whisper(video_url, language)
        elif chosen_method == "api":
            # Force YouTube API
            transcript_result = self._transcribe_with_api(video_url, language)
        else:
            # Auto mode: try API first, fall back to Whisper
            transcript_result = self._transcribe_auto(video_url, language)

        # Merge results
        result.update(transcript_result)

        # Calculate quality score
        if result.get("success"):
            result["quality_score"] = self._calculate_quality_score(result)

        return result

    def _transcribe_with_api(
        self, video_url: str, language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe using YouTube API"""
        logger.info(f"Attempting transcription with YouTube API: {video_url}")

        languages = [language] if language else None
        result = self.youtube_transcriber.get_transcript(video_url, languages)

        if result and result.get("success"):
            logger.info("YouTube API transcription successful")
            return {
                "success": True,
                "transcript": result["transcript"],
                "full_text": result["full_text"],
                "language": result["language"],
                "method": "api",
                "is_generated": result.get("is_generated", False),
            }
        else:
            error_msg = result.get("message", "Unknown error") if result else "No result"
            logger.warning(f"YouTube API transcription failed: {error_msg}")
            return {
                "success": False,
                "error": result.get("error") if result else "api_failed",
                "message": error_msg,
            }

    def _transcribe_with_whisper(
        self, video_url: str, language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe using Whisper"""
        logger.info(f"Attempting transcription with Whisper: {video_url}")

        result = self.whisper_transcriber.transcribe_video(video_url, language)

        if result and result.get("success"):
            logger.info("Whisper transcription successful")
            return {
                "success": True,
                "transcript": result["segments"],
                "full_text": result["full_text"],
                "language": result["language"],
                "method": "whisper",
                "whisper_model": result["model"],
            }
        else:
            error_msg = result.get("message", "Unknown error") if result else "No result"
            logger.error(f"Whisper transcription failed: {error_msg}")
            return {
                "success": False,
                "error": result.get("error") if result else "whisper_failed",
                "message": error_msg,
            }

    def _transcribe_auto(
        self, video_url: str, language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Auto mode: try API first, fall back to Whisper"""
        logger.info(f"Auto mode: trying YouTube API first for {video_url}")

        # Try YouTube API first
        api_result = self._transcribe_with_api(video_url, language)

        if api_result.get("success"):
            logger.info("Using YouTube API transcript")
            return api_result

        # Fall back to Whisper
        logger.info("YouTube API failed, falling back to Whisper")
        whisper_result = self._transcribe_with_whisper(video_url, language)

        if whisper_result.get("success"):
            logger.info("Using Whisper transcript")
            return whisper_result

        # Both failed
        logger.error("Both transcription methods failed")
        return {
            "success": False,
            "error": "all_methods_failed",
            "message": "Both YouTube API and Whisper transcription failed",
            "api_error": api_result.get("message"),
            "whisper_error": whisper_result.get("message"),
        }

    def get_video_metadata(self, video_url: str) -> Optional[Dict[str, Any]]:
        """
        Extract comprehensive metadata from YouTube video

        Args:
            video_url: YouTube video URL or ID

        Returns:
            Dictionary with video metadata
        """
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)

                metadata = {
                    "id": info.get("id"),
                    "title": info.get("title"),
                    "description": info.get("description"),
                    "channel_name": info.get("uploader") or info.get("channel"),
                    "channel_id": info.get("channel_id"),
                    "upload_date": self._parse_upload_date(info.get("upload_date")),
                    "duration_seconds": info.get("duration"),
                    "view_count": info.get("view_count"),
                    "like_count": info.get("like_count"),
                    "comment_count": info.get("comment_count"),
                    "categories": info.get("categories", []),
                    "tags": info.get("tags", []),
                    "thumbnail": info.get("thumbnail"),
                    "webpage_url": info.get("webpage_url"),
                }

                logger.info(f"Extracted metadata for video: {metadata['id']}")
                return metadata

        except Exception as e:
            logger.error(f"Error extracting video metadata: {str(e)}")
            return None

    def _parse_upload_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse upload date from yt-dlp format (YYYYMMDD)"""
        if not date_str:
            return None

        try:
            return datetime.strptime(str(date_str), "%Y%m%d")
        except Exception:
            return None

    def _calculate_quality_score(self, result: Dict[str, Any]) -> float:
        """
        Calculate quality score for transcript (0.0 to 1.0)

        Factors:
        - Method used (manual > API > Whisper)
        - Transcript length vs video duration
        - Language confidence (for Whisper)
        """
        score = 0.5  # Base score

        # Method bonus
        method = result.get("method")
        if method == "api":
            if not result.get("is_generated", False):
                score += 0.3  # Manual captions
            else:
                score += 0.2  # Auto-generated captions
        elif method == "whisper":
            score += 0.1  # Whisper transcription

        # Length check
        duration = result.get("metadata", {}).get("duration_seconds", 0)
        transcript_length = len(result.get("full_text", ""))

        if duration > 0:
            # Expect roughly 150 words per minute, 5 chars per word
            expected_length = (duration / 60) * 150 * 5
            if transcript_length > expected_length * 0.5:
                score += 0.2

        # Cap at 1.0
        return min(1.0, score)

    def get_available_transcripts(self, video_url: str) -> Optional[Dict[str, Any]]:
        """Get information about available transcripts"""
        return self.youtube_transcriber.get_available_transcripts(video_url)

    def batch_transcribe(
        self, video_urls: List[str], method: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Transcribe multiple videos

        Args:
            video_urls: List of YouTube video URLs
            method: Transcription method to use

        Returns:
            List of transcription results
        """
        results = []
        for url in video_urls:
            logger.info(f"Transcribing video {len(results) + 1}/{len(video_urls)}")
            result = self.transcribe(url, method=method)
            results.append(result)

        return results
