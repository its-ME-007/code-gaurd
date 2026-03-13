from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # Application
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    
    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: str
    aws_secret_access_key: str
    dry_run: bool = False
    
    # CORS
    cors_origins: List[str] = ["http://localhost", "http://localhost:3000", "http://localhost:8000"]
    
    # Security
    api_key_enabled: bool = False
    api_key: str = ""
    
    # Feature Flags
    graceful_failure_handling: bool = True
    audit_logging_enabled: bool = True
    key_age_analysis_enabled: bool = True
    
    # Demo User Credentials
    demo_access_key_id: str = ""
    demo_secret_access_key: str = ""
    
    # API Config
    api_title: str = "Cloud Key Rotation Engine"
    api_version: str = "1.0.0"
    
    # Database Configuration
    database_url: str = "sqlite:///./audit_records.db"
    database_echo: bool = False  # Set to True for SQL logging
    
    class Config:
        env_file = ".env" # check out later 
        case_sensitive = False
        extra = "ignore"
    
    @property
    def demo_iam_user(self) -> str:
        """IAM username for demo user"""
        return "demo-user"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()