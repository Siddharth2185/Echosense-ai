"""
Delete API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
import os

from database.connection import get_db
from models import Call
from services.s3_handler import S3Handler

router = APIRouter()
s3_handler = S3Handler()


@router.delete("/{call_id}")
async def delete_call(
    call_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a call and all related data
    
    This will:
    - Delete the call record from database
    - Cascade delete all transcripts, quality scores, and compliance flags
    - Delete the audio file from storage
    """
    # Find the call
    call = db.query(Call).filter(Call.id == call_id).first()
    
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    try:
        # Extract filename from audio_url for deletion
        audio_url = call.audio_url
        if audio_url:
            # Extract filename from URL (last part after /)
            filename = audio_url.split("/")[-1]
            
            # Delete audio file from storage
            await s3_handler.delete_file(filename)
        
        # Delete from database (cascade will handle related records)
        db.delete(call)
        db.commit()
        
        return {
            "success": True,
            "message": "Call deleted successfully",
            "call_id": str(call_id)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to delete call: {str(e)}"
        )
