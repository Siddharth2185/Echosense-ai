"""
Configuration management for Echosense AI backend
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/echosense"
    mongodb_url: str = "mongodb://localhost:27017/echosense_analytics"
    
    # AWS S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket_name: str = "echosense-audio-files"
    
    # MinIO (local S3 alternative)
    minio_endpoint: str = "http://localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    use_minio: bool = True  # Set to False for production AWS S3
    
    # OpenAI
    openai_api_key: str = ""
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Application
    backend_port: int = 8000
    debug: bool = True
    secret_key: str = "change-this-in-production"
    
    # AI Models
    whisper_model_size: str = "base"  # tiny, base, small, medium, large
    use_gpu: bool = False
    max_audio_length_minutes: int = 60
    
    # Processing
    max_concurrent_jobs: int = 5
    processing_timeout_minutes: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
