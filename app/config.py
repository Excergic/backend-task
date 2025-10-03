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
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


settings = Settings()
