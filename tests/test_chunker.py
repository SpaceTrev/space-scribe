"""Tests for chunking functionality"""
import pytest
from core.chunker.chunker import Chunker


class TestChunker:
    """Test chunker"""

    @pytest.fixture
    def chunker(self):
        """Create chunker instance"""
        return Chunker(chunk_sizes=[100, 200], overlap_percent=15)

    @pytest.fixture
    def sample_transcript(self):
        """Sample transcript data"""
        return [
            {"text": "This is sentence one.", "start": 0, "end": 2, "duration": 2},
            {"text": "This is sentence two.", "start": 2, "end": 4, "duration": 2},
            {"text": "This is sentence three.", "start": 4, "end": 6, "duration": 2},
            {"text": "This is sentence four.", "start": 6, "end": 8, "duration": 2},
        ]

    def test_initialization(self, chunker):
        """Test chunker initialization"""
        assert chunker.chunk_sizes == [100, 200]
        assert chunker.overlap_percent == 15

    def test_token_based_chunking(self, chunker, sample_transcript):
        """Test token-based chunking"""
        full_text = " ".join([seg["text"] for seg in sample_transcript])

        chunks = chunker.chunk_transcript(
            sample_transcript, full_text, strategy="token_based", chunk_size=20
        )

        assert len(chunks) > 0
        assert all("chunk_index" in chunk for chunk in chunks)
        assert all("text" in chunk for chunk in chunks)
        assert all("token_count" in chunk for chunk in chunks)

    def test_time_based_chunking(self, chunker, sample_transcript):
        """Test time-based chunking"""
        chunks = chunker._chunk_time_based(sample_transcript, interval_seconds=4)

        assert len(chunks) > 0
        assert chunks[0]["strategy"] == "time_based"

    def test_chunk_creation(self, chunker, sample_transcript):
        """Test chunk creation"""
        chunk = chunker._create_chunk(sample_transcript[:2], index=0, strategy="test")

        assert chunk["chunk_index"] == 0
        assert chunk["strategy"] == "test"
        assert len(chunk["text"]) > 0
        assert chunk["start_time"] == 0
        assert chunk["token_count"] > 0

    def test_split_into_sentences(self, chunker):
        """Test sentence splitting"""
        text = "This is sentence one. This is sentence two! Is this sentence three?"

        sentences = chunker._split_into_sentences(text)

        assert len(sentences) == 3

    def test_count_tokens(self, chunker):
        """Test token counting"""
        text = "This is a test sentence with ten words here today."

        token_count = chunker._count_tokens(text)

        assert token_count > 0
        assert token_count == len(text.split())
