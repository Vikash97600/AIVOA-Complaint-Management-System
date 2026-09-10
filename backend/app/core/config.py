from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "AIVOA"
    ENVIRONMENT: str = "development"
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Database connection string (PostgreSQL default)
    DATABASE_URL: str = "postgresql+psycopg://username:password@localhost:5432/aivoa"
    
    # Groq API configuration
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "gemma2-9b-it"
    
    # Frontend URL for CORS
    FRONTEND_URL: str = "http://localhost:5173"
    
    # Max upload size (10 MB)
    MAX_UPLOAD_SIZE: int = 10485760
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
