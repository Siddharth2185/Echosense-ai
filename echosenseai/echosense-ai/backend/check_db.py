from database.connection import SessionLocal
from models import Call, ProcessingStatus

db = SessionLocal()
calls = db.query(Call).all()
print(f"Total calls: {len(calls)}")
for call in calls:
    print(f"Call ID: {call.id}, Status: {call.status}, Filename: {call.filename}")
db.close()
