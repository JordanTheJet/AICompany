"""Application settings and configuration"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "AICompany Social Media Integration"
    app_env: str = "development"
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Twitter/X API
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    twitter_access_token: Optional[str] = None
    twitter_access_token_secret: Optional[str] = None
    twitter_bearer_token: Optional[str] = None

    # Instagram API
    instagram_username: Optional[str] = None
    instagram_password: Optional[str] = None
    instagram_session_id: Optional[str] = None

    # TikTok API
    tiktok_client_key: Optional[str] = None
    tiktok_client_secret: Optional[str] = None
    tiktok_access_token: Optional[str] = None

    # Database
    database_url: str = "sqlite:///./aicompany.db"

    # Security
    secret_key: str = "your-secret-key-change-this-in-production"
    encryption_key: Optional[str] = None

    # Rate Limiting
    rate_limit_per_minute: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
