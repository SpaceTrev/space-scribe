"""
Basic usage examples for SpaceScribe
"""

from core.transcriber.transcriber import Transcriber
from core.processor.nlp_processor import NLPProcessor
from core.processor.trading_processor import TradingProcessor
from core.chunker.chunker import Chunker


def example_1_basic_transcription():
    """Example 1: Basic video transcription"""
    print("=" * 60)
    print("Example 1: Basic Video Transcription")
    print("=" * 60)

    # Initialize transcriber
    transcriber = Transcriber(default_method="auto")

    # Transcribe a video
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = transcriber.transcribe(video_url)

    if result.get("success"):
        print(f"✓ Video ID: {result['video_id']}")
        print(f"✓ Title: {result['metadata']['title']}")
        print(f"✓ Method: {result['method']}")
        print(f"✓ Language: {result['language']}")
        print(f"✓ Transcript length: {len(result['full_text'])} characters")
        print(f"\nPreview:\n{result['full_text'][:200]}...")
    else:
        print(f"✗ Transcription failed: {result.get('message')}")


def example_2_nlp_processing():
    """Example 2: NLP processing of transcript"""
    print("\n" + "=" * 60)
    print("Example 2: NLP Processing")
    print("=" * 60)

    # Get a transcript (from example 1)
    transcriber = Transcriber()
    result = transcriber.transcribe("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    if not result.get("success"):
        print("Skipping - transcription failed")
        return

    # Process with NLP
    nlp_processor = NLPProcessor()
    nlp_result = nlp_processor.process_transcript(result["full_text"])

    print(f"\n✓ Found {len(nlp_result['entities'])} entities")
    print(f"✓ Extracted {len(nlp_result['keywords'])} keywords")
    print(f"✓ Identified {len(nlp_result['topics'])} topics")

    print("\nTop 5 Keywords:")
    for kw in nlp_result["keywords"][:5]:
        print(f"  - {kw['keyword']} (frequency: {kw['frequency']})")

    print("\nTop 5 Entities:")
    for ent in nlp_result["entities"][:5]:
        print(f"  - {ent['text']} ({ent['label']})")


def example_3_trading_analysis():
    """Example 3: Trading-specific analysis"""
    print("\n" + "=" * 60)
    print("Example 3: Trading Analysis")
    print("=" * 60)

    # Sample trading content
    sample_text = """
    In this video, we'll discuss using RSI and MACD indicators for day trading.
    We'll look at the 5-minute and 15-minute timeframes on forex pairs.
    Risk management is crucial - always use stop loss orders.
    We'll analyze breakout patterns and trend following strategies.
    """

    trading_processor = TradingProcessor()
    result = trading_processor.process_trading_content(sample_text)

    print(f"\n✓ Is trading content: {result['is_trading_content']}")
    print(f"✓ Relevance score: {result['relevance_score']}")

    if result["indicators"]:
        print("\nIndicators mentioned:")
        for ind in result["indicators"]:
            print(f"  - {ind['concept']} ({ind['mentions']} times)")

    if result["timeframes"]:
        print("\nTimeframes mentioned:")
        for tf in result["timeframes"]:
            print(f"  - {tf['concept']}")

    if result["strategies"]:
        print("\nStrategies mentioned:")
        for strat in result["strategies"]:
            print(f"  - {strat['concept']}")


def example_4_chunking():
    """Example 4: Smart chunking"""
    print("\n" + "=" * 60)
    print("Example 4: Smart Chunking")
    print("=" * 60)

    # Sample transcript
    sample_transcript = [
        {"text": "Hello and welcome to this tutorial.", "start": 0, "end": 3, "duration": 3},
        {"text": "Today we'll learn about trading.", "start": 3, "end": 6, "duration": 3},
        {"text": "First, let's discuss indicators.", "start": 6, "end": 9, "duration": 3},
    ]

    sample_text = " ".join([seg["text"] for seg in sample_transcript])

    # Create chunks
    chunker = Chunker(chunk_sizes=[50, 100], overlap_percent=15)

    # Token-based chunking
    chunks = chunker.chunk_transcript(
        sample_transcript, sample_text, strategy="token_based", chunk_size=50
    )

    print(f"\n✓ Created {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i + 1}:")
        print(f"  Token count: {chunk['token_count']}")
        print(f"  Time: {chunk['start_time']:.1f}s - {chunk['end_time']:.1f}s")
        print(f"  Text: {chunk['text'][:60]}...")


def example_5_batch_processing():
    """Example 5: Batch processing multiple videos"""
    print("\n" + "=" * 60)
    print("Example 5: Batch Processing")
    print("=" * 60)

    video_urls = [
        "https://www.youtube.com/watch?v=VIDEO_ID_1",
        "https://www.youtube.com/watch?v=VIDEO_ID_2",
        "https://www.youtube.com/watch?v=VIDEO_ID_3",
    ]

    transcriber = Transcriber()
    results = transcriber.batch_transcribe(video_urls, method="auto")

    successful = sum(1 for r in results if r.get("success"))
    print(f"\n✓ Processed {len(video_urls)} videos")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {len(video_urls) - successful}")

    for i, result in enumerate(results):
        status = "✓" if result.get("success") else "✗"
        video_id = result.get("video_id", "unknown")
        print(f"  {status} Video {i + 1}: {video_id}")


def example_6_database_operations():
    """Example 6: Database operations"""
    print("\n" + "=" * 60)
    print("Example 6: Database Operations")
    print("=" * 60)

    from database.database import SessionLocal
    from database.models import Transcript, Tag
    from sqlalchemy import func

    db = SessionLocal()

    # Get statistics
    total_transcripts = db.query(func.count(Transcript.id)).scalar()
    total_tags = db.query(func.count(Tag.id)).scalar()

    print(f"\n✓ Total transcripts: {total_transcripts}")
    print(f"✓ Total tags: {total_tags}")

    # Get recent transcripts
    recent = (
        db.query(Transcript)
        .order_by(Transcript.created_at.desc())
        .limit(5)
        .all()
    )

    print("\nRecent transcripts:")
    for t in recent:
        print(f"  - {t.title} ({t.video_id})")

    # Search by tag
    trading_transcripts = (
        db.query(Transcript)
        .join(Tag)
        .filter(Tag.tag_category == "trading_indicator")
        .distinct()
        .limit(5)
        .all()
    )

    print(f"\nTranscripts with trading indicators: {len(trading_transcripts)}")

    db.close()


if __name__ == "__main__":
    print("\nSpaceScribe - Usage Examples\n")

    # Run examples
    try:
        example_1_basic_transcription()
    except Exception as e:
        print(f"Example 1 failed: {e}")

    try:
        example_2_nlp_processing()
    except Exception as e:
        print(f"Example 2 failed: {e}")

    try:
        example_3_trading_analysis()
    except Exception as e:
        print(f"Example 3 failed: {e}")

    try:
        example_4_chunking()
    except Exception as e:
        print(f"Example 4 failed: {e}")

    # Skip batch and database examples if not needed
    # example_5_batch_processing()
    # example_6_database_operations()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
