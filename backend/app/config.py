from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ChangeRadar API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./changeradar.db"
    frontend_origin: str = "http://localhost:5173"

    # Session & Security Settings
    session_expire_days: int = 7
    session_cookie_name: str = "session_token"
    session_cookie_samesite: str = "lax"
    session_cookie_secure: Optional[bool] = None  # None = auto-detect based on env / scheme
    rate_limit_auth_requests: int = 20  # Max auth attempts per minute per IP

    # Repository Storage & Deployment Architecture
    allow_local_dev_scanning: bool = True  # Allowed in development; disabled in production
    repo_storage_dir: str = "./storage/repos"
    max_repo_files: int = 5000
    max_repo_size_bytes: int = 50 * 1024 * 1024  # 50MB
    # GitHub Integration Settings
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    github_app_id: Optional[str] = None
    github_private_key: Optional[str] = None
    github_webhook_secret: Optional[str] = None

    # Secret Encryption Key for Stored Credentials (Fernet 32-byte urlsafe base64)
    encryption_key: Optional[str] = None

    # CORS & Deployment
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    analysis_engine_version: str = "1.0.0"
    background_worker_concurrency: int = 4

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
