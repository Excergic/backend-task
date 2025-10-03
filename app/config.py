from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App
    APP_NAME: str = "Stories Service"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/stories_db"
    DB_POOL_MIN_SIZE: int = 10
    DB_POOL_MAX_SIZE: int = 20
    
    # JWT
    JWT_SECRET: str  # Must be set in .env
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Story settings
    STORY_EXPIRATION_HOURS: int = 24

    MINIO_ENDPOINT: str = "http://localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "stories-media"
    MINIO_REGION: str = "us-east-1"
    MINIO_USE_SSL: bool = False

    ALLOWED_CONTENT_TYPES: list[str] = [
        "image/jpeg",
        "image/jpg", 
        "image/png",
        "image/gif",
        "image/webp",
        "video/mp4",
        "video/quicktime",
        "video/webm"
    ]
    MAX_UPLOAD_SIZE_MB: int = 50  # 50MB max
    PRESIGNED_URL_EXPIRATION: int = 3600
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


settings = Settings()
