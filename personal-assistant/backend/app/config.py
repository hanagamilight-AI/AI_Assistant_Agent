"""
Configuration module for the AI Personal Assistant application.

This module provides a centralized configuration system using Pydantic Settings.
All configuration values are loaded from environment variables with sensible defaults.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment",
    )
    app_name: str = Field(default="AI Personal Assistant", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # Database - supports both PostgreSQL and SQLite
    database_url: str = Field(
        default="sqlite+aiosqlite:///./personal_assistant.db",
        description="Database URL (PostgreSQL or SQLite)",
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql+", "sqlite+")):
            raise ValueError("Database URL must start with 'postgresql+' or 'sqlite+'")
        return v

    # Redis (optional)
    redis_url: RedisDsn | None = Field(
        default=None,
        description="Redis connection URL",
    )

    # LLM Configuration
    llm_provider: Literal["openai", "groq", "anthropic", "local"] = Field(
        default="groq",
        description="LLM provider",
    )
    llm_api_key: str = Field(
        default="",
        description="LLM API key",
    )
    llm_model: str = Field(
        default="gpt-4-turbo-preview",
        description="LLM model identifier",
    )
    llm_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="LLM temperature for response generation",
    )
    llm_max_tokens: int = Field(
        default=4096,
        gt=0,
        description="Maximum tokens for LLM response",
    )

    # Embedding Configuration
    embedding_provider: Literal["openai", "local"] = Field(
        default="openai",
        description="Embedding model provider",
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model identifier",
    )

    # Security
    jwt_secret: str = Field(
        default="change-this-secret-in-production",
        description="Secret key for JWT token generation",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration time in minutes",
    )

    # MCP Configuration
    mcp_config_path: str | None = Field(
        default=None,
        description="Path to MCP configuration file",
    )

    # File Storage
    upload_dir: str = Field(
        default="./uploads",
        description="Directory for file uploads",
    )
    max_file_size_mb: int = Field(
        default=50,
        description="Maximum file size in MB",
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    log_format: Literal["json", "text"] = Field(
        default="json",
        description="Log format",
    )

    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=60,
        description="Rate limit per minute",
    )

    # CORS
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Allowed CORS origins (comma-separated)",
    )

    @field_validator("allowed_origins")
    @classmethod
    def parse_allowed_origins(cls, v: str) -> list[str]:
        """Parse comma-separated origins into a list."""
        if isinstance(v, list):
            return v
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Convenience export
settings = get_settings()
