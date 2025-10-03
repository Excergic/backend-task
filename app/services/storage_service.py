import uuid
from typing import Optional
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from app.config import settings


class MinIOStorageService:
    """MinIO storage operations (S3-compatible)"""
    
    def __init__(self):
        """Initialize MinIO client"""
        self.minio_client = boto3.client(
            's3',
            endpoint_url=settings.MINIO_ENDPOINT,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name=settings.MINIO_REGION,
            config=Config(signature_version='s3v4'),
            use_ssl=settings.MINIO_USE_SSL
        )
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create MinIO bucket if it doesn't exist"""
        try:
            self.minio_client.head_bucket(Bucket=settings.MINIO_BUCKET)
            print(f"MinIO bucket exists: {settings.MINIO_BUCKET}")
        except ClientError:
            try:
                self.minio_client.create_bucket(Bucket=settings.MINIO_BUCKET)
                print(f"Created MinIO bucket: {settings.MINIO_BUCKET}")
            except ClientError as e:
                print(f"MinIO bucket creation failed: {e}")
    
    def generate_presigned_upload_url(
        self,
        content_type: str,
        file_extension: str
    ) -> dict:
        """
        Generate MinIO presigned upload URL
        
        Args:
            content_type: MIME type (e.g., 'image/jpeg')
            file_extension: File extension (e.g., 'jpg')
        
        Returns:
            dict with upload_url, fields, and media_key
        """
        # Validate content type
        if content_type not in settings.ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Content type '{content_type}' not allowed. "
                       f"Allowed: {', '.join(settings.ALLOWED_CONTENT_TYPES)}"
            )
        
        # Generate unique object key with stories/ prefix
        unique_id = str(uuid.uuid4())
        object_key = f"stories/{unique_id}.{file_extension}"
        
        try:
            # Generate presigned POST URL for direct upload to MinIO
            presigned_post = self.minio_client.generate_presigned_post(
                Bucket=settings.MINIO_BUCKET,
                Key=object_key,
                Fields={
                    "Content-Type": content_type
                },
                Conditions=[
                    {"Content-Type": content_type},
                    ["content-length-range", 1, settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024]
                ],
                ExpiresIn=settings.PRESIGNED_URL_EXPIRATION
            )
            
            return {
                "upload_url": presigned_post["url"],
                "fields": presigned_post["fields"],
                "media_key": object_key,
                "expires_in": settings.PRESIGNED_URL_EXPIRATION
            }
        
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate MinIO upload URL: {str(e)}"
            )
    
    def generate_presigned_download_url(self, media_key: str) -> str:
        """
        Generate MinIO presigned download URL
        
        Args:
            media_key: Object key in MinIO (e.g., 'stories/uuid.jpg')
        
        Returns:
            Presigned download URL (valid for 1 hour)
        """
        try:
            url = self.minio_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.MINIO_BUCKET,
                    'Key': media_key
                },
                ExpiresIn=3600  # 1 hour
            )
            return url
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate MinIO download URL: {str(e)}"
            )
    
    def delete_media(self, media_key: str) -> bool:
        """
        Delete media from MinIO storage
        
        Args:
            media_key: Object key to delete
        
        Returns:
            True if deleted successfully
        """
        try:
            self.minio_client.delete_object(
                Bucket=settings.MINIO_BUCKET,
                Key=media_key
            )
            print(f"Deleted from MinIO: {media_key}")
            return True
        except ClientError as e:
            print(f"Failed to delete {media_key} from MinIO: {e}")
            return False
    
    def check_media_exists(self, media_key: str) -> bool:
        """Check if media exists in MinIO"""
        try:
            self.minio_client.head_object(
                Bucket=settings.MINIO_BUCKET,
                Key=media_key
            )
            return True
        except ClientError:
            return False
    
    def get_media_metadata(self, media_key: str) -> Optional[dict]:
        """Get metadata for media object in MinIO"""
        try:
            response = self.minio_client.head_object(
                Bucket=settings.MINIO_BUCKET,
                Key=media_key
            )
            return {
                "content_type": response.get("ContentType"),
                "content_length": response.get("ContentLength"),
                "last_modified": response.get("LastModified"),
                "etag": response.get("ETag")
            }
        except ClientError:
            return None


# Global MinIO storage service instance
minio_storage = MinIOStorageService()
