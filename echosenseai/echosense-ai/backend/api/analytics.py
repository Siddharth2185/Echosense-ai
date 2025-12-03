"""
Analytics and reporting API endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Optional

from database.connection import get_db
from models import Call, QualityScore, ComplianceFlag, ProcessingStatus

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(
    days: int = Query(7, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Total calls
    total_calls = db.query(func.count(Call.id)).filter(
        Call.uploaded_at >= since_date
    ).scalar()
    
    # Processed calls
    processed_calls = db.query(func.count(Call.id)).filter(
        Call.uploaded_at >= since_date,
        Call.status == ProcessingStatus.COMPLETED
    ).scalar()
    
    # Average quality score
    avg_quality = db.query(func.avg(QualityScore.overall_score)).join(
        Call
    ).filter(
        Call.uploaded_at >= since_date
    ).scalar()
    
    # Total compliance flags
    total_flags = db.query(func.count(ComplianceFlag.id)).join(
        Call
    ).filter(
        Call.uploaded_at >= since_date
    ).scalar()
    
    # High severity flags
    high_severity_flags = db.query(func.count(ComplianceFlag.id)).join(
        Call
    ).filter(
        Call.uploaded_at >= since_date,
        ComplianceFlag.severity.in_(["high", "critical"])
    ).scalar()
    
    # Average processing time
    avg_processing_time = db.query(
        func.avg(
            func.extract('epoch', Call.processed_at - Call.uploaded_at)
        )
    ).filter(
        Call.uploaded_at >= since_date,
        Call.status == ProcessingStatus.COMPLETED
    ).scalar()
    
    return {
        "period_days": days,
        "total_calls": total_calls or 0,
        "processed_calls": processed_calls or 0,
        "processing_rate": (processed_calls / total_calls * 100) if total_calls else 0,
        "avg_quality_score": round(avg_quality, 2) if avg_quality else None,
        "total_compliance_flags": total_flags or 0,
        "high_severity_flags": high_severity_flags or 0,
        "avg_processing_time_seconds": round(avg_processing_time, 2) if avg_processing_time else None
    }


@router.get("/recent-calls")
async def get_recent_calls(
    limit: int = Query(10, le=100),
    db: Session = Depends(get_db)
):
    """Get recent calls with basic info"""
    calls = db.query(Call).order_by(
        desc(Call.uploaded_at)
    ).limit(limit).all()
    
    results = []
    for call in calls:
        quality = db.query(QualityScore).filter(
            QualityScore.call_id == call.id
        ).first()
        
        results.append({
            "call_id": str(call.id),
            "filename": call.filename,
            "duration": call.duration,
            "status": call.status,
            "uploaded_at": call.uploaded_at,
            "overall_score": quality.overall_score if quality else None
        })
    
    return {"calls": results}


@router.get("/quality-trends")
async def get_quality_trends(
    days: int = Query(30, description="Number of days"),
    db: Session = Depends(get_db)
):
    """Get quality score trends over time"""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Daily average scores
    daily_scores = db.query(
        func.date(Call.uploaded_at).label('date'),
        func.avg(QualityScore.overall_score).label('avg_score'),
        func.count(Call.id).label('call_count')
    ).join(
        QualityScore
    ).filter(
        Call.uploaded_at >= since_date,
        Call.status == ProcessingStatus.COMPLETED
    ).group_by(
        func.date(Call.uploaded_at)
    ).order_by(
        func.date(Call.uploaded_at)
    ).all()
    
    return {
        "trends": [
            {
                "date": str(row.date),
                "avg_score": round(row.avg_score, 2),
                "call_count": row.call_count
            }
            for row in daily_scores
        ]
    }


@router.get("/compliance-summary")
async def get_compliance_summary(
    days: int = Query(7, description="Number of days"),
    db: Session = Depends(get_db)
):
    """Get compliance flag summary"""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Flags by type
    flags_by_type = db.query(
        ComplianceFlag.flag_type,
        func.count(ComplianceFlag.id).label('count')
    ).join(
        Call
    ).filter(
        Call.uploaded_at >= since_date
    ).group_by(
        ComplianceFlag.flag_type
    ).all()
    
    # Flags by severity
    flags_by_severity = db.query(
        ComplianceFlag.severity,
        func.count(ComplianceFlag.id).label('count')
    ).join(
        Call
    ).filter(
        Call.uploaded_at >= since_date
    ).group_by(
        ComplianceFlag.severity
    ).all()
    
    return {
        "by_type": [
            {"type": row.flag_type, "count": row.count}
            for row in flags_by_type
        ],
        "by_severity": [
            {"severity": row.severity, "count": row.count}
            for row in flags_by_severity
        ]
    }
