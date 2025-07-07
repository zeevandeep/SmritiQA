"""
Configuration settings for the Smriti application.

This module loads and provides access to environment variables
and other configuration settings for the application.
"""
import os
from typing import List
from datetime import timedelta

from pydantic import Field, EmailStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings
    APP_NAME: str = "Smriti"
    DEBUG: bool = Field(default=False)
    ENABLE_DOCS: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")
    CORS_ORIGINS: List[str] = ["*"]
    
    # API settings
    API_V1_PREFIX: str = "/api/v1"
    
    # Database settings
    POSTGRES_USER: str = Field(default=os.environ.get("PGUSER"))
    POSTGRES_PASSWORD: str = Field(default=os.environ.get("PGPASSWORD"))
    POSTGRES_HOST: str = Field(default=os.environ.get("PGHOST"))
    POSTGRES_PORT: str = Field(default=os.environ.get("PGPORT", "5432"))
    POSTGRES_DB: str = Field(default=os.environ.get("PGDATABASE"))
    
    @computed_field
    def DATABASE_URL(self) -> str:
        """Generate database URL from connection parameters."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # OpenAI settings
    OPENAI_API_KEY: str = Field(default=os.environ.get("OPENAI_API_KEY"))
    
    # Settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Create settings object
settings = Settings()

# Token Configuration
AUTH_CONFIG = {
    "ACCESS_TOKEN_EXPIRY": timedelta(minutes=30),
    "REFRESH_TOKEN_EXPIRY": timedelta(days=90),
    "ACCESS_TOKEN_MAX_AGE": 1800,      # 30 minutes in seconds
    "REFRESH_TOKEN_MAX_AGE": 7776000,  # 90 days in seconds
}

# Environment detection for cookie security
IS_PRODUCTION = os.getenv("ENV") == "production" or not os.getenv("REPL_ID")