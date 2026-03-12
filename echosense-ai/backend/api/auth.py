"""
Auth API: /api/auth/register and /api/auth/login
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import hashlib
import hmac
import os

from database.connection import get_db
from models import User

router = APIRouter()


# ── Simple password hashing (no bcrypt dependency required) ──────────────────

def _hash_password(password: str) -> str:
    """SHA-256 hash with a random salt, stored as 'salt$hash'."""
    salt = os.urandom(16).hex()
    digest = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${digest}"


def _verify_password(password: str, stored: str) -> bool:
    """Verify a password against the stored 'salt$hash' string."""
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    expected = hashlib.sha256((salt + password).encode()).hexdigest()
    return hmac.compare_digest(expected, digest)


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Create a new user account."""
    # Reject if email already taken
    existing = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        hashed_password=_hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Account created successfully.", "email": user.email}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Validate credentials and return success."""
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()

    # Same error for both "not found" and "wrong password" (security best practice)
    if not user or not _verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    return {"message": "Signed in successfully.", "name": user.name, "email": user.email}
