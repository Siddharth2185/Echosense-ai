"""
Processing status and results API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from database.connection import get_db
from models import Call, Transcript, QualityScore, ComplianceFlag, ReviewComment, ProcessingStatus

router = APIRouter()


@router.get("/status/{call_id}")
async def get_processing_status(
    call_id: UUID,
    db: Session = Depends(get_db)
):
    """Get the processing status of a call"""
    call = db.query(Call).filter(Call.id == call_id).first()
    
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    return {
        "call_id": str(call.id),
        "filename": call.filename,
        "status": call.status,
        "uploaded_at": call.uploaded_at,
        "processed_at": call.processed_at,
        "duration": call.duration,
        "error_message": call.error_message
    }


@router.get("/transcript/{call_id}")
async def get_transcript(
    call_id: UUID,
    db: Session = Depends(get_db)
):
    """Get the full transcript of a call with sentiment analysis"""
    call = db.query(Call).filter(Call.id == call_id).first()
    
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    transcripts = db.query(Transcript).filter(
        Transcript.call_id == call_id
    ).order_by(Transcript.start_time).all()
    
    return {
        "call_id": str(call.id),
        "filename": call.filename,
        "duration": call.duration,
        "status": call.status,
        "transcript": [
            {
                "speaker": t.speaker,
                "text": t.text,
                "start_time": t.start_time,
                "end_time": t.end_time,
                "sentiment": t.sentiment,
                "sentiment_score": t.sentiment_score
            }
            for t in transcripts
        ]
    }


@router.get("/quality/{call_id}")
async def get_quality_score(
    call_id: UUID,
    db: Session = Depends(get_db)
):
    """Get quality scores for a call"""
    quality = db.query(QualityScore).filter(
        QualityScore.call_id == call_id
    ).first()
    
    if not quality:
        raise HTTPException(status_code=404, detail="Quality score not found")
    
    return {
        "call_id": str(call_id),
        "overall_score": quality.overall_score,
        "politeness_score": quality.politeness_score,
        "clarity_score": quality.clarity_score,
        "empathy_score": quality.empathy_score,
        "resolution_score": quality.resolution_score,
        "script_adherence_score": quality.script_adherence_score,
        "avg_sentiment": quality.avg_sentiment,
        "silence_duration": quality.silence_duration,
        "overlap_duration": quality.overlap_duration
    }


@router.get("/compliance/{call_id}")
async def get_compliance_flags(
    call_id: UUID,
    db: Session = Depends(get_db)
):
    """Get compliance flags for a call"""
    flags = db.query(ComplianceFlag).filter(
        ComplianceFlag.call_id == call_id
    ).order_by(ComplianceFlag.timestamp).all()
    
    return {
        "call_id": str(call_id),
        "total_flags": len(flags),
        "flags": [
            {
                "type": f.flag_type,
                "description": f.description,
                "severity": f.severity,
                "timestamp": f.timestamp
            }
            for f in flags
        ]
    }


@router.get("/full-report/{call_id}")
async def get_full_report(
    call_id: UUID,
    db: Session = Depends(get_db)
):
    """Get complete analysis report for a call"""
    call = db.query(Call).filter(Call.id == call_id).first()
    
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Get all related data
    transcripts = db.query(Transcript).filter(
        Transcript.call_id == call_id
    ).order_by(Transcript.start_time).all()
    
    quality = db.query(QualityScore).filter(
        QualityScore.call_id == call_id
    ).first()
    
    flags = db.query(ComplianceFlag).filter(
        ComplianceFlag.call_id == call_id
    ).all()
    
    # Get review comments
    reviews = db.query(ReviewComment).filter(
        ReviewComment.call_id == call_id
    ).order_by(ReviewComment.created_at).all()
    
    return {
        "call_info": {
            "call_id": str(call.id),
            "filename": call.filename,
            "duration": call.duration,
            "status": call.status,
            "uploaded_at": call.uploaded_at,
            "processed_at": call.processed_at
        },
        "transcript": [
            {
                "speaker": t.speaker,
                "text": t.text,
                "start_time": t.start_time,
                "end_time": t.end_time,
                "sentiment": t.sentiment,
                "sentiment_score": t.sentiment_score
            }
            for t in transcripts
        ],
        "quality_scores": {
            "overall_score": quality.overall_score if quality else None,
            "politeness_score": quality.politeness_score if quality else None,
            "clarity_score": quality.clarity_score if quality else None,
            "empathy_score": quality.empathy_score if quality else None,
            "resolution_score": quality.resolution_score if quality else None,
            "script_adherence_score": quality.script_adherence_score if quality else None,
            "avg_sentiment": quality.avg_sentiment if quality else None
        } if quality else None,
        "compliance_flags": [
            {
                "type": f.flag_type,
                "description": f.description,
                "severity": f.severity,
                "timestamp": f.timestamp
            }
            for f in flags
        ],
        "review_comments": [
            {
                "id": str(r.id),
                "reviewer_name": r.reviewer_name,
                "category": r.category,
                "comment": r.comment,
                "score_override": r.score_override,
                "created_at": r.created_at
            }
            for r in reviews
        ]
    }

@router.post("/reprocess/{call_id}")
async def reprocess_call(
    call_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Force re-process a call — resets status and re-queues processing."""
    call = db.query(Call).filter(Call.id == call_id).first()

    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    # Delete existing transcript data so it can be re-generated cleanly
    db.query(Transcript).filter(Transcript.call_id == call_id).delete()
    db.query(QualityScore).filter(QualityScore.call_id == call_id).delete()
    db.query(ComplianceFlag).filter(ComplianceFlag.call_id == call_id).delete()

    call.status = ProcessingStatus.UPLOADED
    call.error_message = None
    call.processed_at = None
    db.commit()

    from services.call_processor import processor
    background_tasks.add_task(processor.process_call, str(call_id))

    return {
        "call_id": str(call_id),
        "message": "Call queued for re-processing.",
        "status": "uploaded"
    }


# ── Pydantic schema for review comment creation ──
class ReviewCommentCreate(BaseModel):
    reviewer_name: str = "Reviewer"
    category: str = "general"
    comment: str
    score_override: Optional[float] = None


@router.post("/review/{call_id}")
async def add_review_comment(
    call_id: UUID,
    body: ReviewCommentCreate,
    db: Session = Depends(get_db)
):
    """Add a training / review comment to a call"""
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    review = ReviewComment(
        call_id=call_id,
        reviewer_name=body.reviewer_name,
        category=body.category,
        comment=body.comment,
        score_override=body.score_override
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    return {
        "id": str(review.id),
        "call_id": str(call_id),
        "reviewer_name": review.reviewer_name,
        "category": review.category,
        "comment": review.comment,
        "score_override": review.score_override,
        "created_at": review.created_at
    }


@router.get("/reviews/{call_id}")
async def get_review_comments(
    call_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all review / training comments for a call"""
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    reviews = db.query(ReviewComment).filter(
        ReviewComment.call_id == call_id
    ).order_by(ReviewComment.created_at).all()

    return {
        "call_id": str(call_id),
        "total": len(reviews),
        "reviews": [
            {
                "id": str(r.id),
                "reviewer_name": r.reviewer_name,
                "category": r.category,
                "comment": r.comment,
                "score_override": r.score_override,
                "created_at": r.created_at
            }
            for r in reviews
        ]
    }
