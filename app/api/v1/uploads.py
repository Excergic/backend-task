from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.config import settings
from app.api.deps import get_current_user_id
from app.models.schemas import (
    GenerateUploadUrlRequest,
    GenerateUploadUrlResponse,
    GetDownloadUrlRequest,
    GetDownloadUrlResponse
)
from app.services.storage_service import minio_storage


router = APIRouter(prefix="/media", tags=["Media Storage"])


@router.post("/upload-url", response_model=GenerateUploadUrlResponse)
async def get_presigned_upload_url(
    data: GenerateUploadUrlRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)]
):
    """
    Generate MinIO presigned URL for direct media upload
    
    **Upload Flow:**
    1. Request presigned URL from this endpoint
    2. Upload file directly to MinIO (not through API)
    3. Use returned media_key when creating story
    
    **Supported formats:**
    - Images: JPEG, PNG, GIF, WebP
    - Videos: MP4, QuickTime, WebM
    
    **Limits:**
    - Max size: 50MB
    - URL expires in: 1 hour
    """
    result = minio_storage.generate_presigned_upload_url(
        content_type=data.content_type,
        file_extension=data.file_extension
    )
    
    return GenerateUploadUrlResponse(**result)


@router.post("/download-url", response_model=GetDownloadUrlResponse)
async def get_presigned_download_url(
    data: GetDownloadUrlRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)]
):
    """
    Generate MinIO presigned URL for downloading media
    
    Returns temporary download URL valid for 1 hour
    """
    # Check if media exists in MinIO
    if not minio_storage.check_media_exists(data.media_key):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found in MinIO storage"
        )
    
    download_url = minio_storage.generate_presigned_download_url(data.media_key)
    
    return GetDownloadUrlResponse(
        download_url=download_url,
        expires_in=3600
    )


@router.get("/metadata/{media_key:path}")
async def get_media_metadata(
    media_key: str,
    user_id: Annotated[UUID, Depends(get_current_user_id)]
):
    """
    Get metadata for media object in MinIO
    
    Returns content type, size, last modified, etc.
    """
    metadata = minio_storage.get_media_metadata(media_key)
    
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found in MinIO"
        )
    
    return metadata


@router.get("/health")
async def minio_health_check():
    """Check MinIO service connectivity"""
    try:
        # Test connection by listing buckets
        minio_storage.minio_client.list_buckets()
        return {
            "status": "healthy",
            "service": "MinIO",
            "endpoint": settings.MINIO_ENDPOINT,
            "bucket": settings.MINIO_BUCKET
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"MinIO service unavailable: {str(e)}"
        )
