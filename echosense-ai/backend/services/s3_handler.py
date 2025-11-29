"""
S3/MinIO file storage handler
"""
import boto3
from botocore.exceptions import ClientError
from io import BytesIO
from typing import Optional

from config import get_settings

settings = get_settings()


class S3Handler:
    """Handle file uploads to S3 or MinIO"""
    
    def __init__(self):
        self.client = None
        self.bucket_name = None
        self._initialized = False
        self._init_error = None
        
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
            print("[WARNING] File upload features will be disabled")
    
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
    
    async def upload_file(self, file_content: bytes, filename: str) -> str:
        """
        Upload file to S3/MinIO
        
        Args:
            file_content: File bytes
            filename: Unique filename
            
        Returns:
            URL to the uploaded file
        """
        if not self._initialized:
            raise Exception(f"S3/MinIO storage not available: {self._init_error}")
        
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
            raise Exception(f"Failed to upload file: {str(e)}")
    
    async def download_file(self, filename: str) -> bytes:
        """Download file from S3/MinIO"""
        if not self._initialized:
            raise Exception(f"S3/MinIO storage not available: {self._init_error}")
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=filename
            )
            return response['Body'].read()
        except Exception as e:
            raise Exception(f"Failed to download file: {str(e)}")
    
    async def delete_file(self, filename: str) -> bool:
        """Delete file from S3/MinIO"""
        if not self._initialized:
            print(f"[WARNING] S3/MinIO storage not available: {self._init_error}")
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
