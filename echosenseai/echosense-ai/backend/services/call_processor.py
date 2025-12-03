"""
Call processing service (Mock/Simplified for local dev)
"""
import asyncio
import random
from datetime import datetime
import time
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
            
            try:
                call.status = ProcessingStatus.PROCESSING
                db.commit()
                
                # Mock Transcript
                transcript_text = "Hello, thank you for calling Echosense AI support. How can I help you today? I'm having trouble with my account. I understand, let me check that for you."
                
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
                        "text": "I'm having trouble with my account.",
                        "start": 6.0,
                        "end": 8.5,
                        "sentiment": SentimentType.NEUTRAL
                    },
                    {
                        "speaker": "Agent",
                        "text": "I understand, let me check that for you.",
                        "start": 9.0,
                        "end": 12.0,
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
                
                # Mock Quality Score
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
                
                # Mock Compliance Flag (maybe)
                if random.random() > 0.7:
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
                call.status = ProcessingStatus.FAILED
                call.error_message = str(e)
                db.commit()

# Create a simple async task wrapper to mimic Celery's .delay()
class AsyncTask:
    def __init__(self, func):
        self.func = func
    
    def delay(self, *args, **kwargs):
        # In a real app, this would send to Celery
        # Here we just fire and forget using asyncio.create_task if there's a running loop
        # or just run it? 
        # Since we are in FastAPI, we can use BackgroundTasks, but the code imports this directly.
        # We'll hack it to run in the background.
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self.func(*args, **kwargs))
        except RuntimeError:
            # No loop running (e.g. script), just run sync
            asyncio.run(self.func(*args, **kwargs))

processor = CallProcessor()
process_call_async = AsyncTask(processor.process_call)
