"""
Call processing service (Mock/Simplified for local dev)
"""
import random
from datetime import datetime
import time
import threading
from sqlalchemy.orm import Session

from database.connection import get_db_context
from models import Call, ProcessingStatus, QualityScore, Transcript, ComplianceFlag, SentimentType

class CallProcessor:
    """Mock call processor for local development"""
    
    def process_call(self, call_id: str):
        """
        Process a call (Mock implementation)
        """
        import uuid as uuid_lib
        
        # Convert string to UUID if needed
        if isinstance(call_id, str):
            call_id = uuid_lib.UUID(call_id)
        
        print(f"[INFO] Starting processing for call {call_id}")
        
        # Simulate processing time (optimized for faster results)
        # For real AI processing, optimize by:
        # - Using smaller Whisper models (tiny/base instead of large)
        # - Batch processing multiple segments in parallel
        # - GPU acceleration if available
        # - Caching frequently used models in memory
        time.sleep(0.5)  # Reduced from 2 seconds for faster processing
        
        with get_db_context() as db:
            call = db.query(Call).filter(Call.id == call_id).first()
            if not call:
                print(f"[ERROR] Call {call_id} not found")
                return
            
            # ── Idempotency guard: skip if already processed or being processed ──
            if call.status in (ProcessingStatus.COMPLETED, ProcessingStatus.PROCESSING):
                # Check if transcripts already exist to avoid duplicates
                existing_transcripts = db.query(Transcript).filter(
                    Transcript.call_id == call_id
                ).count()
                if existing_transcripts > 0:
                    print(f"[INFO] Call {call_id} already has {existing_transcripts} transcript(s). Skipping re-processing.")
                    return
            
            try:
                call.status = ProcessingStatus.PROCESSING
                db.commit()
                
                # Create mock transcript segments
                segments = [
                    {
                        "speaker": "Agent",
                        "text": "Hello, thank you for calling Echosense AI support. How can I help you today?",
                        "start": 0.0,
                        "end": 5.5,
                        "sentiment": SentimentType.POSITIVE
                    },
                    {
                        "speaker": "Customer",
                        "text": "I'm having trouble with my account. I can't seem to log into the portal.",
                        "start": 6.0,
                        "end": 9.2,
                        "sentiment": SentimentType.NEUTRAL
                    },
                    {
                        "speaker": "Agent",
                        "text": "I understand, let me check that for you. Can I have your email address please?",
                        "start": 9.5,
                        "end": 13.0,
                        "sentiment": SentimentType.POSITIVE
                    },
                    {
                        "speaker": "Customer",
                        "text": "Sure, it's john.doe@example.com.",
                        "start": 13.5,
                        "end": 15.5,
                        "sentiment": SentimentType.NEUTRAL
                    },
                    {
                        "speaker": "Agent",
                        "text": "Thank you! I can see your account here. It looks like your password needs to be reset. I'll send you a reset link right now.",
                        "start": 16.0,
                        "end": 22.0,
                        "sentiment": SentimentType.POSITIVE
                    },
                    {
                        "speaker": "Customer",
                        "text": "Oh great, thank you so much! That was quick.",
                        "start": 22.5,
                        "end": 25.0,
                        "sentiment": SentimentType.POSITIVE
                    },
                    {
                        "speaker": "Agent",
                        "text": "You're welcome! Is there anything else I can help you with today?",
                        "start": 25.5,
                        "end": 28.5,
                        "sentiment": SentimentType.POSITIVE
                    },
                    {
                        "speaker": "Customer",
                        "text": "No, that's everything. Thanks again!",
                        "start": 29.0,
                        "end": 31.0,
                        "sentiment": SentimentType.POSITIVE
                    }
                ]
                
                for seg in segments:
                    transcript = Transcript(
                        call_id=call.id,
                        speaker=seg["speaker"],
                        text=seg["text"],
                        start_time=seg["start"],
                        end_time=seg["end"],
                        sentiment=seg["sentiment"],
                        sentiment_score=0.8 if seg["sentiment"] == SentimentType.POSITIVE else 0.0
                    )
                    db.add(transcript)
                
                # Mock Quality Score (only add if not already present)
                existing_quality = db.query(QualityScore).filter(
                    QualityScore.call_id == call_id
                ).first()
                if not existing_quality:
                    quality = QualityScore(
                        call_id=call.id,
                        overall_score=85.5,
                        politeness_score=90.0,
                        clarity_score=88.0,
                        empathy_score=82.0,
                        resolution_score=80.0,
                        script_adherence_score=95.0,
                        avg_sentiment=0.6,
                        silence_duration=2.5,
                        overlap_duration=0.5
                    )
                    db.add(quality)
                
                # Mock Compliance Flag (maybe, only if none exist)
                existing_flags = db.query(ComplianceFlag).filter(
                    ComplianceFlag.call_id == call_id
                ).count()
                if existing_flags == 0 and random.random() > 0.5:
                    flag = ComplianceFlag(
                        call_id=call.id,
                        flag_type="long_pause",
                        description="Detected silence longer than 10 seconds",
                        severity="low",
                        timestamp=15.0
                    )
                    db.add(flag)
                
                call.status = ProcessingStatus.COMPLETED
                call.processed_at = datetime.utcnow()
                db.commit()
                print(f"[INFO] Completed processing for call {call_id}")
                
            except Exception as e:
                print(f"[ERROR] Processing failed: {e}")
                import traceback
                traceback.print_exc()
                try:
                    call.status = ProcessingStatus.FAILED
                    call.error_message = str(e)
                    db.commit()
                except Exception as inner_e:
                    print(f"[ERROR] Could not update call status: {inner_e}")

# Create a simple background task wrapper to mimic Celery's .delay()
# Runs the synchronous process_call in a daemon thread so it doesn't block FastAPI.
class AsyncTask:
    def __init__(self, func):
        self.func = func
    
    def delay(self, *args, **kwargs):
        """Fire-and-forget: run func in a background daemon thread."""
        t = threading.Thread(target=self.func, args=args, kwargs=kwargs, daemon=True)
        t.start()
        return t

processor = CallProcessor()
process_call_async = AsyncTask(processor.process_call)
