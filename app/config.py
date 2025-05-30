# app/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application
    app_name: str = "PromptHub"
    version: str = "1.0.0"
    debug: bool = False
    
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "prompthub"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # LLM Providers
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 768
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # File Upload
    max_upload_size_mb: int = 10
    allowed_file_types: list = [".pdf", ".txt", ".md"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()