"""Whisper-based transcription for videos without captions"""
import logging
import os
import tempfile
from typing import Optional, Dict, Any, List
import yt_dlp
import whisper
from pathlib import Path

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """Handle transcription using OpenAI Whisper"""

    def __init__(self, model_name: str = "base", device: Optional[str] = None):
        """
        Initialize Whisper transcriber

        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            device: Device to run on ('cuda' or 'cpu', auto-detect if None)
        """
        self.model_name = model_name
        self.device = device
        self._model = None
        logger.info(f"Initialized Whisper transcriber with model: {model_name}")

    @property
    def model(self):
        """Lazy load Whisper model"""
        if self._model is None:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self._model = whisper.load_model(self.model_name, device=self.device)
            logger.info("Whisper model loaded successfully")
        return self._model

    def download_audio(self, video_url: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Download audio from YouTube video

        Args:
            video_url: YouTube video URL
            output_path: Path to save audio file (temp file if None)

        Returns:
            Path to downloaded audio file or None if failed
        """
        try:
            if output_path is None:
                # Create temporary directory
                temp_dir = tempfile.mkdtemp()
                output_path = os.path.join(temp_dir, "audio.%(ext)s")

            ydl_opts = {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
                "outtmpl": output_path,
                "quiet": True,
                "no_warnings": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)

                # Find the actual output file
                if output_path.endswith(".%(ext)s"):
                    base_path = output_path.replace(".%(ext)s", "")
                    audio_file = f"{base_path}.mp3"
                else:
                    audio_file = output_path

                if os.path.exists(audio_file):
                    logger.info(f"Audio downloaded successfully: {audio_file}")
                    return audio_file
                else:
                    logger.error(f"Audio file not found after download: {audio_file}")
                    return None

        except Exception as e:
            logger.error(f"Error downloading audio: {str(e)}")
            return None

    def transcribe_audio(
        self, audio_path: str, language: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio file using Whisper

        Args:
            audio_path: Path to audio file
            language: Language code (auto-detect if None)

        Returns:
            Transcription result with segments and text
        """
        try:
            logger.info(f"Transcribing audio with Whisper: {audio_path}")

            # Transcribe with Whisper
            result = self.model.transcribe(
                audio_path,
                language=language,
                verbose=False,
                word_timestamps=True,
            )

            # Format segments
            formatted_segments = self._format_segments(result["segments"])

            return {
                "language": result["language"],
                "text": result["text"],
                "segments": formatted_segments,
                "full_text": result["text"],
                "method": "whisper",
                "model": self.model_name,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return {
                "success": False,
                "error": "transcription_failed",
                "message": str(e),
            }

    def transcribe_video(
        self, video_url: str, language: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Download and transcribe a YouTube video

        Args:
            video_url: YouTube video URL
            language: Language code (auto-detect if None)

        Returns:
            Transcription result
        """
        audio_path = None
        try:
            # Download audio
            logger.info(f"Downloading audio from: {video_url}")
            audio_path = self.download_audio(video_url)

            if not audio_path:
                return {
                    "success": False,
                    "error": "download_failed",
                    "message": "Failed to download audio",
                }

            # Transcribe
            result = self.transcribe_audio(audio_path, language)

            if result and result.get("success"):
                # Extract video ID for consistency
                from core.transcriber.youtube_transcriber import YouTubeTranscriber
                yt = YouTubeTranscriber()
                video_id = yt.extract_video_id(video_url)
                result["video_id"] = video_id

            return result

        except Exception as e:
            logger.error(f"Error in transcribe_video: {str(e)}")
            return {
                "success": False,
                "error": "unknown_error",
                "message": str(e),
            }

        finally:
            # Clean up audio file
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                    # Remove temp directory if empty
                    temp_dir = os.path.dirname(audio_path)
                    if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                        os.rmdir(temp_dir)
                except Exception as e:
                    logger.warning(f"Error cleaning up audio file: {str(e)}")

    def _format_segments(self, segments: List[Dict]) -> List[Dict[str, Any]]:
        """
        Format Whisper segments to match YouTube transcript format

        Args:
            segments: Raw Whisper segments

        Returns:
            Formatted segments
        """
        formatted = []
        for segment in segments:
            formatted.append(
                {
                    "text": segment["text"].strip(),
                    "start": segment["start"],
                    "end": segment["end"],
                    "duration": segment["end"] - segment["start"],
                }
            )
        return formatted

    def get_supported_models(self) -> List[str]:
        """Get list of supported Whisper models"""
        return ["tiny", "base", "small", "medium", "large"]

    def estimate_processing_time(self, duration_seconds: int) -> float:
        """
        Estimate processing time based on video duration and model size

        Args:
            duration_seconds: Video duration in seconds

        Returns:
            Estimated processing time in seconds
        """
        # Rough estimates (actual time varies by hardware)
        model_multipliers = {
            "tiny": 0.1,
            "base": 0.2,
            "small": 0.4,
            "medium": 0.8,
            "large": 1.5,
        }

        multiplier = model_multipliers.get(self.model_name, 0.5)
        return duration_seconds * multiplier
