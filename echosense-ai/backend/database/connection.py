"""
Database connection management — SQLite local dev mode
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator, Optional
import warnings
import os

from config import get_settings

settings = get_settings()

# ──────────────────────────────────────────────
# SQLite / PostgreSQL engine setup
# ──────────────────────────────────────────────
engine: Optional[any] = None
SessionLocal: Optional[any] = None

db_url: str = settings.database_url

try:
    if db_url.startswith("sqlite"):
        # SQLite does NOT support pool_size / max_overflow
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},  # needed for FastAPI threading
            pool_pre_ping=True,
        )

        # Enable WAL mode for better concurrent read performance
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.execute("PRAGMA cache_size=-64000;")   # 64 MB cache
            cursor.execute("PRAGMA temp_store=MEMORY;")
            cursor.close()

        print("[OK] SQLite connection established")

    else:
        # PostgreSQL / other databases — use full pooling
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        print("[OK] PostgreSQL connection established")

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

except Exception as e:
    warnings.warn(f"[WARNING] Database not available: {e}. Running in limited mode.")
    print(f"[WARNING] Database not available: {e}")

# ──────────────────────────────────────────────
# MongoDB — OPTIONAL, skip gracefully if not running
# ──────────────────────────────────────────────
mongo_client = None
mongo_db = None

_mongo_url = settings.mongodb_url
if _mongo_url and _mongo_url.strip():
    try:
        from pymongo import MongoClient
        mongo_client = MongoClient(_mongo_url, serverSelectionTimeoutMS=500)
        mongo_client.server_info()          # quick ping
        mongo_db = mongo_client.get_database()
        print("[OK] MongoDB connection established")
    except Exception:
        # MongoDB is completely optional — silence the warning
        mongo_client = None
        mongo_db = None
        print("[INFO] MongoDB not available — skipping (SQLite is primary DB).")


# ──────────────────────────────────────────────
# Session helpers
# ──────────────────────────────────────────────

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency — yields a SQLAlchemy session.
    Falls back cleanly if SessionLocal is None.
    """
    if SessionLocal is None:
        raise RuntimeError(
            "Database not available. Check DATABASE_URL in .env"
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context-manager version of get_db for use outside FastAPI routes.

    Usage:
        with get_db_context() as db:
            ...
    """
    if SessionLocal is None:
        raise RuntimeError(
            "Database not available. Check DATABASE_URL in .env"
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables defined by the SQLAlchemy models."""
    if engine is None:
        print("[WARNING] Skipping DB init — no engine configured.")
        return
    try:
        from models import Base
        Base.metadata.create_all(bind=engine)
        print("[OK] Database tables created / verified successfully")
    except Exception as e:
        print(f"[WARNING] Could not initialise database tables: {e}")


if __name__ == "__main__":
    init_db()
