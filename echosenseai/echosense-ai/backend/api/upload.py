"""
File upload API endpoints
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from database.connection import get_db
from models import Call, ProcessingStatus
from services.s3_handler import S3Handler
from services.audio_processor import AudioProcessor

router = APIRouter()
s3_handler = S3Handler()
audio_processor = AudioProcessor()


@router.post("/audio")
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload an audio file for processing
    
    Accepts: MP3, WAV, M4A, OGG, FLAC
    Max size: 100MB
    """
    # Validate file type
    allowed_extensions = [".mp3", ".wav", ".m4a", ".ogg", ".flac"]
    file_ext = "." + file.filename.split(".")[-1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (100MB max)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    max_size = 100 * 1024 * 1024  # 100MB
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {max_size / (1024*1024)}MB"
        )
    
    try:
        # Generate unique filename
        call_id = uuid.uuid4()
        unique_filename = f"{call_id}{file_ext}"
        
        # Upload to S3
        file_content = await file.read()
        audio_url = await s3_handler.upload_file(
            file_content=file_content,
            filename=unique_filename
        )
        
        # Get audio duration
        duration = audio_processor.get_duration(file_content)
        
        # Create database record
        call = Call(
            id=call_id,
            audio_url=audio_url,
            filename=file.filename,
            duration=duration,
            status=ProcessingStatus.UPLOADED
        )
        
        db.add(call)
        db.commit()
        db.refresh(call)
        
        # Trigger async processing
        from services.call_processor import processor
        background_tasks.add_task(processor.process_call, str(call_id))
        
        return {
            "call_id": str(call_id),
            "filename": file.filename,
            "duration": duration,
            "status": call.status,
            "message": "File uploaded successfully. Processing started."
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/bulk")
async def upload_bulk_audio(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload multiple audio files for batch processing
    """
    results = []
    
    for file in files:
        try:
            result = await upload_audio(background_tasks, file, db)
            results.append({"filename": file.filename, "success": True, "data": result})
        except Exception as e:
            results.append({"filename": file.filename, "success": False, "error": str(e)})
    
    return {
        "total": len(files),
        "successful": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results
    }
