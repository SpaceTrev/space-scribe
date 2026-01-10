from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    ForeignKey,
    JSON,
    Index,
    Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.database import Base


class Transcript(Base):
    """Main transcript table storing video transcripts and metadata"""

    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(20), unique=True, index=True, nullable=False)
    youtube_url = Column(String(500), nullable=False)
    title = Column(String(500))
    channel_name = Column(String(200))
    channel_id = Column(String(50))
    upload_date = Column(DateTime)
    duration_seconds = Column(Integer)
    view_count = Column(Integer)
    transcript_full = Column(Text)
    transcript_method = Column(String(20))  # 'api' or 'whisper'
    language = Column(String(10))
    quality_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    metadata_json = Column(JSON)

    # Processing flags
    nlp_processed = Column(Boolean, default=False)
    chunks_created = Column(Boolean, default=False)
    tags_extracted = Column(Boolean, default=False)

    # Relationships
    chunks = relationship("Chunk", back_populates="transcript", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="transcript", cascade="all, delete-orphan")

    # Indexes for better query performance
    __table_args__ = (
        Index("idx_video_id", "video_id"),
        Index("idx_channel_id", "channel_id"),
        Index("idx_language", "language"),
        Index("idx_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<Transcript(id={self.id}, video_id={self.video_id}, title={self.title})>"


class Chunk(Base):
    """Chunked transcript data for LLM consumption"""

    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    start_time = Column(Float)
    end_time = Column(Float)
    word_count = Column(Integer)
    token_count = Column(Integer)
    strategy = Column(String(20))  # 'time_based', 'topic_based', 'token_based'
    metadata_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    transcript = relationship("Transcript", back_populates="chunks")

    # Indexes
    __table_args__ = (
        Index("idx_transcript_id", "transcript_id"),
        Index("idx_chunk_index", "chunk_index"),
    )

    def __repr__(self):
        return f"<Chunk(id={self.id}, transcript_id={self.transcript_id}, index={self.chunk_index})>"


class Tag(Base):
    """Tags and entities extracted from transcripts"""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"), nullable=False)
    tag_name = Column(String(100), nullable=False, index=True)
    tag_category = Column(String(50), index=True)  # 'strategy', 'indicator', 'concept', etc.
    confidence_score = Column(Float)
    entity_type = Column(String(50))  # 'PERSON', 'ORG', 'GPE', 'TECHNICAL', etc.
    context = Column(Text)  # Surrounding text where tag was found
    metadata_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    transcript = relationship("Transcript", back_populates="tags")

    # Indexes
    __table_args__ = (
        Index("idx_transcript_id_tag", "transcript_id"),
        Index("idx_tag_name", "tag_name"),
        Index("idx_tag_category", "tag_category"),
    )

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.tag_name}, category={self.tag_category})>"


class Job(Base):
    """Background job tracking for async operations"""

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(50), unique=True, index=True, nullable=False)
    job_type = Column(String(20), nullable=False)  # 'single', 'batch', 'playlist'
    status = Column(String(20), default="pending", index=True)  # 'pending', 'processing', 'completed', 'failed'
    progress_percent = Column(Float, default=0.0)
    video_urls = Column(JSON)  # List of video URLs to process
    results_json = Column(JSON)  # Results or errors
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    user_id = Column(String(50))  # For multi-user support

    # Additional metadata
    total_videos = Column(Integer)
    processed_videos = Column(Integer, default=0)
    failed_videos = Column(Integer, default=0)
    metadata_json = Column(JSON)

    # Indexes
    __table_args__ = (
        Index("idx_job_id", "job_id"),
        Index("idx_status", "status"),
        Index("idx_created_at_jobs", "created_at"),
    )

    def __repr__(self):
        return f"<Job(id={self.id}, job_id={self.job_id}, type={self.job_type}, status={self.status})>"
