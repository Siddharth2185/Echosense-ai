"""
Database connection management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator, Optional
from pymongo import MongoClient
import warnings

from config import get_settings

settings = get_settings()

# PostgreSQL connection (optional - will be None if psycopg2 not available)
engine: Optional[any] = None
SessionLocal: Optional[any] = None

try:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("[OK] PostgreSQL connection established")
except Exception as e:
    warnings.warn(f"[WARNING] PostgreSQL not available: {e}. Running in limited mode.")
    print("[WARNING] PostgreSQL not available. Some features will be disabled.")

# MongoDB connection (for analytics and logs)
mongo_client: Optional[any] = None
mongo_db: Optional[any] = None

try:
    mongo_client = MongoClient(settings.mongodb_url, serverSelectionTimeoutMS=2000)
    # Test connection
    mongo_client.server_info()
    mongo_db = mongo_client.get_database()
    print("[OK] MongoDB connection established")
except Exception as e:
    warnings.warn(f"[WARNING] MongoDB not available: {e}. Running in limited mode.")
    print("[WARNING] MongoDB not available. Some features will be disabled.")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get database session
    
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    if SessionLocal is None:
        raise RuntimeError("Database not available. Please configure PostgreSQL.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database session
    
    Usage:
        with get_db_context() as db:
            ...
    """
    if SessionLocal is None:
        raise RuntimeError("Database not available. Please configure PostgreSQL.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    if engine is None:
        print("[WARNING] Skipping database initialization - PostgreSQL not available")
        return
    try:
        from models import Base
        Base.metadata.create_all(bind=engine)
        print("[OK] Database tables created successfully")
    except Exception as e:
        print(f"[WARNING] Could not initialize database: {e}")


if __name__ == "__main__":
    init_db()
