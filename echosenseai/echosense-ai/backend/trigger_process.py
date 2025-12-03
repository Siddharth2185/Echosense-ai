"""Trigger processing for all pending calls"""
from database.connection import SessionLocal
from models import Call, ProcessingStatus
from services.call_processor import processor

db = SessionLocal()
calls = db.query(Call).filter(Call.status == ProcessingStatus.UPLOADED).all()
print(f"Found {len(calls)} pending calls")

for call in calls:
    print(f"Processing call {call.id}...")
    processor.process_call(str(call.id))
    print(f"Completed call {call.id}")

db.close()
print("All done!")
