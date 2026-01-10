"""Tests for transcription functionality"""
import pytest
from core.transcriber.youtube_transcriber import YouTubeTranscriber
from core.transcriber.transcriber import Transcriber


class TestYouTubeTranscriber:
    """Test YouTube transcriber"""

    def test_extract_video_id(self):
        """Test video ID extraction from various URL formats"""
        transcriber = YouTubeTranscriber()

        # Standard watch URL
        video_id = transcriber.extract_video_id(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )
        assert video_id == "dQw4w9WgXcQ"

        # Short URL
        video_id = transcriber.extract_video_id("https://youtu.be/dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"

        # Embed URL
        video_id = transcriber.extract_video_id(
            "https://www.youtube.com/embed/dQw4w9WgXcQ"
        )
        assert video_id == "dQw4w9WgXcQ"

        # Just video ID
        video_id = transcriber.extract_video_id("dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"

        # Invalid URL
        video_id = transcriber.extract_video_id("not-a-valid-url")
        assert video_id is None


class TestTranscriber:
    """Test main transcriber"""

    def test_initialization(self):
        """Test transcriber initialization"""
        transcriber = Transcriber(default_method="auto", whisper_model="base")
        assert transcriber.default_method == "auto"
        assert transcriber.whisper_transcriber.model_name == "base"

    def test_quality_score_calculation(self):
        """Test quality score calculation"""
        transcriber = Transcriber()

        # Mock result
        result = {
            "method": "api",
            "is_generated": False,
            "full_text": "a " * 1000,  # 2000 characters
            "metadata": {"duration_seconds": 60},
        }

        score = transcriber._calculate_quality_score(result)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be decent score for manual API transcript
