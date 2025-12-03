"""
Agent training and recommendations API endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict
from datetime import datetime, timedelta

from database.connection import get_db
from models import Call, QualityScore, ComplianceFlag, ProcessingStatus

router = APIRouter()


@router.get("/recommendations")
async def get_training_recommendations(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Generate training recommendations based on call quality analysis
    """
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all completed calls with quality scores
    calls_with_scores = db.query(Call, QualityScore).join(
        QualityScore
    ).filter(
        Call.uploaded_at >= since_date,
        Call.status == ProcessingStatus.COMPLETED
    ).all()
    
    if not calls_with_scores:
        return {
            "total_calls_analyzed": 0,
            "analysis_period_days": days,
            "overall_performance": {
                "average_score": 0,
                "grade": "N/A"
            },
            "training_recommendations": [],
            "focus_areas": []
        }
    
    # Calculate aggregate metrics
    total_calls = len(calls_with_scores)
    avg_overall = sum(qs.overall_score for _, qs in calls_with_scores) / total_calls
    avg_politeness = sum(qs.politeness_score for _, qs in calls_with_scores) / total_calls
    avg_clarity = sum(qs.clarity_score for _, qs in calls_with_scores) / total_calls
    avg_empathy = sum(qs.empathy_score for _, qs in calls_with_scores) / total_calls
    avg_resolution = sum(qs.resolution_score for _, qs in calls_with_scores) / total_calls
    
    # Get compliance flags count
    total_flags = db.query(func.count(ComplianceFlag.id)).join(
        Call
    ).filter(
        Call.uploaded_at >= since_date
    ).scalar() or 0
    
    # Determine weak areas (below 80)
    weak_areas = []
    if avg_politeness < 80:
        weak_areas.append({
            "category": "Politeness",
            "current_score": round(avg_politeness, 1),
            "target_score": 90.0,
            "priority": "high" if avg_politeness < 70 else "medium"
        })
    
    if avg_clarity < 80:
        weak_areas.append({
            "category": "Clarity",
            "current_score": round(avg_clarity, 1),
            "target_score": 90.0,
            "priority": "high" if avg_clarity < 70 else "medium"
        })
    
    if avg_empathy < 80:
        weak_areas.append({
            "category": "Empathy",
            "current_score": round(avg_empathy, 1),
            "target_score": 90.0,
            "priority": "high" if avg_empathy < 70 else "medium"
        })
    
    if avg_resolution < 80:
        weak_areas.append({
            "category": "Resolution",
            "current_score": round(avg_resolution, 1),
            "target_score": 90.0,
            "priority": "high" if avg_resolution < 70 else "medium"
        })
    
    # Generate training recommendations based on weak areas
    training_recommendations = []
    
    # Training modules mapping
    training_modules = {
        "Politeness": {
            "title": "Professional Communication & Etiquette",
            "description": "Improve tone, word choice, and respectful language in customer interactions",
            "topics": [
                "Using positive language and avoiding negative phrases",
                "Active listening techniques",
                "Maintaining professional tone under pressure",
                "Greeting and closing conversations effectively"
            ],
            "estimated_duration": "2 hours"
        },
        "Clarity": {
            "title": "Clear & Concise Communication",
            "description": "Enhance ability to explain complex information in simple terms",
            "topics": [
                "Structuring responses logically",
                "Avoiding jargon and technical language",
                "Confirming customer understanding",
                "Speaking at appropriate pace and volume"
            ],
            "estimated_duration": "1.5 hours"
        },
        "Empathy": {
            "title": "Empathy & Emotional Intelligence",
            "description": "Develop skills to understand and respond to customer emotions",
            "topics": [
                "Recognizing customer emotions from verbal cues",
                "Expressing understanding and acknowledgment",
                "Building rapport quickly",
                "De-escalation techniques for frustrated customers"
            ],
            "estimated_duration": "2.5 hours"
        },
        "Resolution": {
            "title": "Problem-Solving & Resolution Skills",
            "description": "Strengthen ability to resolve customer issues effectively",
            "topics": [
                "Systematic problem identification",
                "Offering appropriate solutions",
                "Setting realistic expectations",
                "Following up on unresolved issues"
            ],
            "estimated_duration": "2 hours"
        }
    }
    
    for area in weak_areas:
        category = area["category"]
        if category in training_modules:
            module = training_modules[category]
            training_recommendations.append({
                "category": category,
                "priority": area["priority"],
                "current_score": area["current_score"],
                "target_score": area["target_score"],
                "module": module
            })
    
    # If no weak areas, suggest advanced training
    if not training_recommendations:
        training_recommendations.append({
            "category": "Advanced Skills",
            "priority": "low",
            "current_score": round(avg_overall, 1),
            "target_score": 95.0,
            "module": {
                "title": "Advanced Customer Service Excellence",
                "description": "Master-level techniques for exceptional customer experiences",
                "topics": [
                    "Anticipating customer needs proactively",
                    "Cross-selling and upselling techniques",
                    "Handling VIP and high-value customers",
                    "Mentoring and coaching other agents"
                ],
                "estimated_duration": "3 hours"
            }
        })
    
    # Determine performance grade
    grade = "A+" if avg_overall >= 95 else "A" if avg_overall >= 90 else "B" if avg_overall >= 80 else "C" if avg_overall >= 70 else "D"
    
    return {
        "total_calls_analyzed": total_calls,
        "analysis_period_days": days,
        "overall_performance": {
            "average_score": round(avg_overall, 1),
            "grade": grade,
            "politeness": round(avg_politeness, 1),
            "clarity": round(avg_clarity, 1),
            "empathy": round(avg_empathy, 1),
            "resolution": round(avg_resolution, 1)
        },
        "compliance_flags": total_flags,
        "training_recommendations": sorted(
            training_recommendations,
            key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["priority"]]
        ),
        "focus_areas": [area["category"] for area in weak_areas[:3]]
    }
