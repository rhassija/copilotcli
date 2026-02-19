"""
Environment configuration management for backend application.
Loads and validates configuration from environment variables.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # GitHub Authentication
    github_token: str = ""
    
    # Application Settings
    env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    # CORS Settings
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Session Configuration
    session_secret_key: str = "dev-secret-key-change-in-production"
    session_expiry_hours: int = 24
    
    # GitHub API Configuration
    github_api_base_url: str = "https://api.github.com"
    github_api_timeout: int = 30
    github_api_max_retries: int = 3
    
    # WebSocket Configuration
    websocket_message_queue_size: int = 1000
    websocket_message_history_minutes: int = 10
    websocket_ping_interval: int = 30
    websocket_ping_timeout: int = 10
    
    # Copilot CLI Configuration
    copilot_cli_path: str = "./src/ui/app.py"
    copilot_cli_timeout_seconds: int = 300
    
    # Rate Limiting
    github_rate_limit_per_hour: int = 1000
    
    # Cache Configuration
    repo_cache_ttl_seconds: int = 300
    branch_cache_ttl_seconds: int = 300
    
    # Security
    https_only: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.env.lower() == "development"

    def validate_github_token(self) -> bool:
        """Validate that GitHub token is set."""
        if not self.github_token or self.github_token == "":
            return False
        if self.github_token.startswith("your_github"):
            return False
        return True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Returns:
        Settings: Application configuration settings
    """
    return Settings()


# Convenience access
settings = get_settings()
