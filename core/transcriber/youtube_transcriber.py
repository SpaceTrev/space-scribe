"""YouTube transcript API handler"""
import logging
from typing import Optional, List, Dict, Any
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)
import re

logger = logging.getLogger(__name__)


class YouTubeTranscriber:
    """Handle transcription using YouTube's built-in captions"""

    def __init__(self, languages: Optional[List[str]] = None):
        """
        Initialize YouTube transcriber

        Args:
            languages: List of language codes to try (e.g., ['en', 'es', 'fr'])
        """
        self.languages = languages or ["en"]

    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from various YouTube URL formats

        Args:
            url: YouTube URL

        Returns:
            Video ID or None if not found
        """
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})",
            r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
            r"youtube\.com/v/([a-zA-Z0-9_-]{11})",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        # If no pattern matches, assume the input is already a video ID
        if re.match(r"^[a-zA-Z0-9_-]{11}$", url):
            return url

        return None

    def get_transcript(
        self, video_url: str, languages: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get transcript for a video using YouTube API

        Args:
            video_url: YouTube video URL or ID
            languages: Override default languages

        Returns:
            Dictionary with transcript data or None if unavailable
        """
        video_id = self.extract_video_id(video_url)
        if not video_id:
            logger.error(f"Could not extract video ID from URL: {video_url}")
            return None

        langs = languages or self.languages

        try:
            # Try to get transcript in preferred languages
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try manual captions first (higher quality)
            try:
                transcript = transcript_list.find_manually_created_transcript(langs)
                transcript_data = transcript.fetch()
                language = transcript.language_code
                is_generated = False
                logger.info(
                    f"Found manual transcript for {video_id} in {language}"
                )
            except NoTranscriptFound:
                # Fall back to auto-generated captions
                transcript = transcript_list.find_generated_transcript(langs)
                transcript_data = transcript.fetch()
                language = transcript.language_code
                is_generated = True
                logger.info(
                    f"Found auto-generated transcript for {video_id} in {language}"
                )

            # Format transcript data
            formatted_transcript = self._format_transcript(transcript_data)

            return {
                "video_id": video_id,
                "language": language,
                "is_generated": is_generated,
                "transcript": formatted_transcript,
                "full_text": " ".join([entry["text"] for entry in formatted_transcript]),
                "method": "api",
                "success": True,
            }

        except TranscriptsDisabled:
            logger.warning(f"Transcripts are disabled for video {video_id}")
            return {
                "video_id": video_id,
                "success": False,
                "error": "transcripts_disabled",
                "message": "Transcripts are disabled for this video",
            }

        except NoTranscriptFound:
            logger.warning(
                f"No transcript found for video {video_id} in languages {langs}"
            )
            return {
                "video_id": video_id,
                "success": False,
                "error": "no_transcript",
                "message": f"No transcript found in languages: {langs}",
            }

        except VideoUnavailable:
            logger.error(f"Video {video_id} is unavailable")
            return {
                "video_id": video_id,
                "success": False,
                "error": "video_unavailable",
                "message": "Video is unavailable",
            }

        except Exception as e:
            logger.error(f"Error getting transcript for {video_id}: {str(e)}")
            return {
                "video_id": video_id,
                "success": False,
                "error": "unknown_error",
                "message": str(e),
            }

    def _format_transcript(self, transcript_data: List[Dict]) -> List[Dict[str, Any]]:
        """
        Format transcript data with cleaned text and timestamps

        Args:
            transcript_data: Raw transcript data from API

        Returns:
            Formatted transcript entries
        """
        formatted = []
        for entry in transcript_data:
            formatted.append(
                {
                    "text": entry["text"].strip(),
                    "start": entry["start"],
                    "duration": entry["duration"],
                    "end": entry["start"] + entry["duration"],
                }
            )
        return formatted

    def get_available_transcripts(self, video_url: str) -> Optional[Dict[str, Any]]:
        """
        Get list of available transcripts for a video

        Args:
            video_url: YouTube video URL or ID

        Returns:
            Dictionary with available transcript information
        """
        video_id = self.extract_video_id(video_url)
        if not video_id:
            return None

        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            manual = []
            generated = []

            for transcript in transcript_list:
                info = {
                    "language": transcript.language,
                    "language_code": transcript.language_code,
                    "is_translatable": transcript.is_translatable,
                }

                if transcript.is_generated:
                    generated.append(info)
                else:
                    manual.append(info)

            return {
                "video_id": video_id,
                "manual_captions": manual,
                "auto_generated": generated,
                "has_transcripts": len(manual) > 0 or len(generated) > 0,
            }

        except Exception as e:
            logger.error(f"Error listing transcripts for {video_id}: {str(e)}")
            return None

    def translate_transcript(
        self, video_url: str, target_language: str, source_language: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get translated transcript

        Args:
            video_url: YouTube video URL or ID
            target_language: Target language code
            source_language: Source language code (optional)

        Returns:
            Translated transcript data
        """
        video_id = self.extract_video_id(video_url)
        if not video_id:
            return None

        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            if source_language:
                transcript = transcript_list.find_transcript([source_language])
            else:
                # Get any available transcript
                transcript = next(iter(transcript_list))

            # Translate if possible
            if transcript.is_translatable:
                translated = transcript.translate(target_language)
                transcript_data = translated.fetch()

                formatted_transcript = self._format_transcript(transcript_data)

                return {
                    "video_id": video_id,
                    "source_language": transcript.language_code,
                    "target_language": target_language,
                    "transcript": formatted_transcript,
                    "full_text": " ".join([entry["text"] for entry in formatted_transcript]),
                    "method": "api_translated",
                    "success": True,
                }
            else:
                logger.warning(f"Transcript for {video_id} is not translatable")
                return None

        except Exception as e:
            logger.error(f"Error translating transcript for {video_id}: {str(e)}")
            return None
