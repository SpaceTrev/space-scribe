"""Smart chunking system for LLM consumption"""
import logging
from typing import List, Dict, Any, Optional
import re

logger = logging.getLogger(__name__)


class Chunker:
    """
    Create chunks from transcripts using various strategies
    for optimal LLM consumption
    """

    def __init__(
        self,
        chunk_sizes: Optional[List[int]] = None,
        overlap_percent: int = 15,
        default_strategy: str = "token_based",
    ):
        """
        Initialize chunker

        Args:
            chunk_sizes: List of target chunk sizes in tokens
            overlap_percent: Overlap percentage between chunks
            default_strategy: Default chunking strategy
        """
        self.chunk_sizes = chunk_sizes or [500, 1000, 2000]
        self.overlap_percent = overlap_percent
        self.default_strategy = default_strategy

        logger.info(
            f"Initialized Chunker with sizes: {chunk_sizes}, "
            f"overlap: {overlap_percent}%, strategy: {default_strategy}"
        )

    def chunk_transcript(
        self,
        transcript: List[Dict[str, Any]],
        full_text: str,
        strategy: Optional[str] = None,
        chunk_size: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Create chunks from transcript

        Args:
            transcript: List of transcript segments with timestamps
            full_text: Full transcript text
            strategy: Chunking strategy ('time_based', 'topic_based', 'token_based')
            chunk_size: Target chunk size in tokens (uses default if None)

        Returns:
            List of chunks with metadata
        """
        strategy = strategy or self.default_strategy
        chunk_size = chunk_size or self.chunk_sizes[0]

        if strategy == "time_based":
            return self._chunk_time_based(transcript, chunk_size)
        elif strategy == "topic_based":
            return self._chunk_topic_based(transcript, full_text, chunk_size)
        elif strategy == "token_based":
            return self._chunk_token_based(transcript, full_text, chunk_size)
        else:
            logger.warning(f"Unknown strategy: {strategy}, using token_based")
            return self._chunk_token_based(transcript, full_text, chunk_size)

    def _chunk_time_based(
        self, transcript: List[Dict[str, Any]], interval_seconds: int = 300
    ) -> List[Dict[str, Any]]:
        """
        Chunk by time intervals

        Args:
            transcript: Transcript segments
            interval_seconds: Time interval for each chunk

        Returns:
            Time-based chunks
        """
        chunks = []
        current_chunk = []
        chunk_start_time = 0
        chunk_index = 0

        for segment in transcript:
            segment_start = segment.get("start", 0)

            # If segment is beyond current interval, create new chunk
            if segment_start >= chunk_start_time + interval_seconds:
                if current_chunk:
                    chunks.append(
                        self._create_chunk(current_chunk, chunk_index, "time_based")
                    )
                    chunk_index += 1

                current_chunk = []
                chunk_start_time = segment_start

            current_chunk.append(segment)

        # Add final chunk
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, chunk_index, "time_based"))

        return chunks

    def _chunk_topic_based(
        self, transcript: List[Dict[str, Any]], full_text: str, target_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Chunk based on topic changes (sentence boundaries + size constraints)

        Args:
            transcript: Transcript segments
            full_text: Full text for sentence detection
            target_size: Target chunk size in tokens

        Returns:
            Topic-based chunks
        """
        # Split into sentences
        sentences = self._split_into_sentences(full_text)

        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0
        overlap_tokens = int(target_size * (self.overlap_percent / 100))

        segment_idx = 0

        for sentence in sentences:
            sentence_tokens = self._count_tokens(sentence)

            # If adding this sentence exceeds target size, create new chunk
            if current_tokens + sentence_tokens > target_size and current_chunk:
                # Find corresponding segments
                chunk_segments = self._find_segments_for_text(
                    " ".join(current_chunk), transcript, segment_idx
                )

                chunks.append(
                    self._create_chunk(chunk_segments, chunk_index, "topic_based")
                )
                chunk_index += 1

                # Keep last few sentences for overlap
                overlap_sentences = []
                overlap_count = 0
                for sent in reversed(current_chunk):
                    sent_tokens = self._count_tokens(sent)
                    if overlap_count + sent_tokens <= overlap_tokens:
                        overlap_sentences.insert(0, sent)
                        overlap_count += sent_tokens
                    else:
                        break

                current_chunk = overlap_sentences
                current_tokens = overlap_count

            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        # Add final chunk
        if current_chunk:
            chunk_segments = self._find_segments_for_text(
                " ".join(current_chunk), transcript, segment_idx
            )
            chunks.append(self._create_chunk(chunk_segments, chunk_index, "topic_based"))

        return chunks

    def _chunk_token_based(
        self, transcript: List[Dict[str, Any]], full_text: str, target_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Chunk by token count with sentence boundary respect

        Args:
            transcript: Transcript segments
            full_text: Full text
            target_size: Target chunk size in tokens

        Returns:
            Token-based chunks
        """
        sentences = self._split_into_sentences(full_text)

        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0
        overlap_tokens = int(target_size * (self.overlap_percent / 100))

        for sentence in sentences:
            sentence_tokens = self._count_tokens(sentence)

            # If this sentence alone is larger than target, split it further
            if sentence_tokens > target_size:
                # If current chunk has content, save it first
                if current_chunk:
                    chunk_segments = self._find_segments_for_text(
                        " ".join(current_chunk), transcript, 0
                    )
                    chunks.append(
                        self._create_chunk(chunk_segments, chunk_index, "token_based")
                    )
                    chunk_index += 1
                    current_chunk = []
                    current_tokens = 0

                # Split large sentence into words
                words = sentence.split()
                word_chunk = []
                word_tokens = 0

                for word in words:
                    word_tokens += 1
                    word_chunk.append(word)

                    if word_tokens >= target_size:
                        chunk_text = " ".join(word_chunk)
                        chunk_segments = self._find_segments_for_text(
                            chunk_text, transcript, 0
                        )
                        chunks.append(
                            self._create_chunk(
                                chunk_segments, chunk_index, "token_based"
                            )
                        )
                        chunk_index += 1

                        # Overlap
                        overlap_words = word_chunk[-overlap_tokens:]
                        word_chunk = overlap_words
                        word_tokens = len(overlap_words)

                if word_chunk:
                    current_chunk = [" ".join(word_chunk)]
                    current_tokens = len(word_chunk)

            # If adding this sentence exceeds target, create new chunk
            elif current_tokens + sentence_tokens > target_size and current_chunk:
                chunk_segments = self._find_segments_for_text(
                    " ".join(current_chunk), transcript, 0
                )
                chunks.append(
                    self._create_chunk(chunk_segments, chunk_index, "token_based")
                )
                chunk_index += 1

                # Create overlap
                overlap_sentences = []
                overlap_count = 0
                for sent in reversed(current_chunk):
                    sent_tokens = self._count_tokens(sent)
                    if overlap_count + sent_tokens <= overlap_tokens:
                        overlap_sentences.insert(0, sent)
                        overlap_count += sent_tokens
                    else:
                        break

                current_chunk = overlap_sentences
                current_tokens = overlap_count
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens

        # Add final chunk
        if current_chunk:
            chunk_segments = self._find_segments_for_text(
                " ".join(current_chunk), transcript, 0
            )
            chunks.append(self._create_chunk(chunk_segments, chunk_index, "token_based"))

        return chunks

    def _create_chunk(
        self, segments: List[Dict[str, Any]], index: int, strategy: str
    ) -> Dict[str, Any]:
        """
        Create chunk object from segments

        Args:
            segments: List of transcript segments
            index: Chunk index
            strategy: Chunking strategy used

        Returns:
            Chunk dictionary
        """
        if not segments:
            return {
                "chunk_index": index,
                "text": "",
                "start_time": 0,
                "end_time": 0,
                "word_count": 0,
                "token_count": 0,
                "strategy": strategy,
            }

        text = " ".join([seg.get("text", "") for seg in segments]).strip()

        return {
            "chunk_index": index,
            "text": text,
            "start_time": segments[0].get("start", 0),
            "end_time": segments[-1].get("end", 0),
            "word_count": len(text.split()),
            "token_count": self._count_tokens(text),
            "strategy": strategy,
            "metadata_json": {
                "segment_count": len(segments),
                "first_segment": segments[0].get("text", "")[:100],
            },
        }

    def _find_segments_for_text(
        self,
        text: str,
        transcript: List[Dict[str, Any]],
        start_idx: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Find transcript segments that match the given text

        Args:
            text: Text to match
            transcript: Full transcript
            start_idx: Start index in transcript

        Returns:
            Matching segments
        """
        # Simple approach: find segments that contain the text
        matching_segments = []
        text_lower = text.lower()

        for i in range(start_idx, len(transcript)):
            segment = transcript[i]
            if segment.get("text", "").lower() in text_lower:
                matching_segments.append(segment)

        # If no matches found, return empty segment
        if not matching_segments:
            return [
                {
                    "text": text,
                    "start": 0,
                    "end": 0,
                    "duration": 0,
                }
            ]

        return matching_segments

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be improved with spaCy)
        # Split on period, exclamation, question mark followed by space
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _count_tokens(self, text: str) -> int:
        """
        Approximate token count (simple word-based)

        Args:
            text: Text to count

        Returns:
            Approximate token count
        """
        # Simple approximation: split on whitespace
        # For more accuracy, use tiktoken or similar
        return len(text.split())

    def create_all_chunk_sizes(
        self, transcript: List[Dict[str, Any]], full_text: str, strategy: Optional[str] = None
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Create chunks for all configured sizes

        Args:
            transcript: Transcript segments
            full_text: Full text
            strategy: Chunking strategy

        Returns:
            Dictionary mapping chunk size to chunks
        """
        all_chunks = {}

        for size in self.chunk_sizes:
            chunks = self.chunk_transcript(transcript, full_text, strategy, size)
            all_chunks[size] = chunks
            logger.info(
                f"Created {len(chunks)} chunks of size {size} using {strategy or self.default_strategy}"
            )

        return all_chunks
