"""
S3/MinIO file storage handler
"""
import boto3
from botocore.exceptions import ClientError
from io import BytesIO
from typing import Optional
import os
import shutil

from config import get_settings

settings = get_settings()


class S3Handler:
    """Handle file uploads to S3, MinIO, or local storage"""
    
    def __init__(self):
        self.client = None
        self.bucket_name = None
        self._initialized = False
        self._init_error = None
        self.use_local_storage = False
        # Use the top-level project `storage` directory so FastAPI static mount can serve files
        self.local_storage_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "storage")
        )
        
        # Try to initialize, but don't fail if services are unavailable
        try:
            if settings.use_minio:
                # Use MinIO for local development
                self.client = boto3.client(
                    's3',
                    endpoint_url=settings.minio_endpoint,
                    aws_access_key_id=settings.minio_access_key,
                    aws_secret_access_key=settings.minio_secret_key,
                    region_name='us-east-1'
                )
                self.bucket_name = "echosense-audio"
            else:
                # Use AWS S3 for production
                self.client = boto3.client(
                    's3',
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=settings.aws_region
                )
                self.bucket_name = settings.s3_bucket_name
            
            # Ensure bucket exists (with timeout)
            self._ensure_bucket_exists()
            self._initialized = True
            print("[OK] S3/MinIO storage initialized")
        except Exception as e:
            self._init_error = str(e)
            print(f"[WARNING] S3/MinIO storage not available: {e}")
            print("[INFO] Falling back to local file storage")
            self.use_local_storage = True
            self._ensure_local_storage_exists()
            self._initialized = True
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        if not self.client:
            return
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            try:
                if settings.use_minio:
                    self.client.create_bucket(Bucket=self.bucket_name)
                else:
                    self.client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': settings.aws_region}
                    )
                print(f"[OK] Created bucket: {self.bucket_name}")
            except Exception as e:
                print(f"[WARNING] Could not create bucket: {e}")
                raise e

    def _ensure_local_storage_exists(self):
        """Create local storage directory if it doesn't exist"""
        if not os.path.exists(self.local_storage_path):
            os.makedirs(self.local_storage_path)
            print(f"[OK] Created local storage directory: {self.local_storage_path}")
    
    async def upload_file(self, file_content: bytes, filename: str) -> str:
        """
        Upload file to S3/MinIO or local storage
        
        Args:
            file_content: File bytes
            filename: Unique filename
            
        Returns:
            URL to the uploaded file
        """
        if not self._initialized:
            raise Exception(f"Storage not available: {self._init_error}")
        
        if self.use_local_storage:
            try:
                file_path = os.path.join(self.local_storage_path, filename)
                with open(file_path, "wb") as f:
                    f.write(file_content)
                # Return a local file URL (served by static mount or similar)
                return f"/storage/{filename}" 
            except Exception as e:
                raise Exception(f"Failed to save file locally: {str(e)}")

        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=BytesIO(file_content),
                ContentType=self._get_content_type(filename)
            )
            
            # Generate URL
            if settings.use_minio:
                url = f"{settings.minio_endpoint}/{self.bucket_name}/{filename}"
            else:
                url = f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{filename}"
            
            return url
            
        except Exception as e:
            # Fallback to local storage if S3 upload fails mid-operation
            print(f"[WARNING] Upload to S3 failed: {e}. Trying local storage.")
            self.use_local_storage = True
            self._ensure_local_storage_exists()
            return await self.upload_file(file_content, filename)
    
    async def download_file(self, filename: str) -> bytes:
        """Download file from S3/MinIO or local storage"""
        if not self._initialized:
            raise Exception(f"Storage not available: {self._init_error}")
            
        if self.use_local_storage:
            try:
                file_path = os.path.join(self.local_storage_path, filename)
                with open(file_path, "rb") as f:
                    return f.read()
            except Exception as e:
                raise Exception(f"Failed to read local file: {str(e)}")

        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=filename
            )
            return response['Body'].read()
        except Exception as e:
             # Fallback to local storage
            if not self.use_local_storage:
                 self.use_local_storage = True
                 return await self.download_file(filename)
            raise Exception(f"Failed to download file: {str(e)}")
    
    async def delete_file(self, filename: str) -> bool:
        """Delete file from S3/MinIO or local storage"""
        if not self._initialized:
            print(f"[WARNING] Storage not available: {self._init_error}")
            return False
            
        if self.use_local_storage:
            try:
                file_path = os.path.join(self.local_storage_path, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
                return False
            except Exception as e:
                print(f"Failed to delete local file: {str(e)}")
                return False

        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=filename
            )
            return True
        except Exception as e:
            print(f"Failed to delete file: {str(e)}")
            return False
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension"""
        ext = filename.split('.')[-1].lower()
        content_types = {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'm4a': 'audio/mp4',
            'ogg': 'audio/ogg',
            'flac': 'audio/flac'
        }
        return content_types.get(ext, 'application/octet-stream')
