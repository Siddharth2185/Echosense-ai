"""
SQLAlchemy ORM models for Echosense AI
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Enum, Uuid
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum


Base = declarative_base()


class ProcessingStatus(str, enum.Enum):
    """Call processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SentimentType(str, enum.Enum):
    """Sentiment classification"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    SATISFIED = "satisfied"


class Call(Base):
    """Call recording metadata"""
    __tablename__ = "calls"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audio_url = Column(Text, nullable=False)
    filename = Column(String(255), nullable=False)
    duration = Column(Integer)  # Duration in seconds
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.UPLOADED)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    transcripts = relationship("Transcript", back_populates="call", cascade="all, delete-orphan")
    quality_score = relationship("QualityScore", back_populates="call", uselist=False, cascade="all, delete-orphan")
    compliance_flags = relationship("ComplianceFlag", back_populates="call", cascade="all, delete-orphan")


class Transcript(Base):
    """Transcript segments with speaker diarization"""
    __tablename__ = "transcripts"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(Uuid(as_uuid=True), ForeignKey("calls.id"), nullable=False)
    speaker = Column(String(20), nullable=False)  # "Agent" or "Customer"
    text = Column(Text, nullable=False)
    start_time = Column(Float, nullable=False)  # Timestamp in seconds
    end_time = Column(Float, nullable=False)
    sentiment = Column(Enum(SentimentType), nullable=True)
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0
    
    # Relationships
    call = relationship("Call", back_populates="transcripts")


class QualityScore(Base):
    """Overall quality metrics for a call"""
    __tablename__ = "quality_scores"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(Uuid(as_uuid=True), ForeignKey("calls.id"), nullable=False, unique=True)
    
    # Overall score (0-100)
    overall_score = Column(Float, nullable=False)
    
    # Individual metrics (0-100)
    politeness_score = Column(Float, nullable=False)
    clarity_score = Column(Float, nullable=False)
    empathy_score = Column(Float, nullable=False)
    resolution_score = Column(Float, nullable=False)
    script_adherence_score = Column(Float, nullable=True)
    
    # Additional metrics
    avg_sentiment = Column(Float, nullable=True)
    silence_duration = Column(Float, nullable=True)  # Total silence in seconds
    overlap_duration = Column(Float, nullable=True)  # Speech overlap in seconds
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    call = relationship("Call", back_populates="quality_score")


class ComplianceFlag(Base):
    """Compliance violations and important events"""
    __tablename__ = "compliance_flags"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(Uuid(as_uuid=True), ForeignKey("calls.id"), nullable=False)
    
    flag_type = Column(String(50), nullable=False)  # e.g., "missed_script", "policy_violation"
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)  # "low", "medium", "high", "critical"
    timestamp = Column(Float, nullable=True)  # When in the call this occurred (seconds)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    call = relationship("Call", back_populates="compliance_flags")


class Agent(Base):
    """Agent information for performance tracking"""
    __tablename__ = "agents"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    employee_id = Column(String(50), unique=True, nullable=True)
    
    # Performance metrics (calculated periodically)
    avg_quality_score = Column(Float, nullable=True)
    total_calls_handled = Column(Integer, default=0)
    compliance_violations = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
