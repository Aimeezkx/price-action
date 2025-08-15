"""
Application configuration settings
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = Field(
        default="postgresql://postgres:password@localhost:5432/document_learning",
        description="PostgreSQL database URL"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for caching and task queue"
    )
    
    # API
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    debug: bool = Field(default=True, description="Debug mode")
    
    # File storage
    upload_dir: str = Field(default="./uploads", description="Upload directory")
    max_file_size: int = Field(default=100 * 1024 * 1024, description="Max file size in bytes (100MB)")
    
    # Processing
    use_llm: bool = Field(default=False, description="Enable LLM processing")
    privacy_mode: bool = Field(default=True, description="Privacy mode - local processing only")
    
    # Privacy and Security
    anonymize_logs: bool = Field(default=True, description="Anonymize sensitive data in logs")
    allowed_file_types: list[str] = Field(
        default=["pdf", "docx", "md"], 
        description="Allowed file types for upload"
    )
    enable_file_scanning: bool = Field(default=True, description="Enable malware scanning")
    log_retention_days: int = Field(default=30, description="Log retention period in days")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()