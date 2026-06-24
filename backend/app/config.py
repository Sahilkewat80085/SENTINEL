import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Config
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    PROJECT_NAME: str = "SENTINEL"
    API_V1_STR: str = "/api/v1"

    # Database Settings
    # Use postgresql+asyncpg:// for async operations in SQLAlchemy
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://sentinel:sentinel_secure_pass@localhost:5432/sentinel_db"
    )

    # Redis Settings
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # GitHub Settings
    GITHUB_PAT: str | None = None

    # Security
    JWT_SECRET: str = Field(
        default="4f4f78328c0b78dfde89c36195c80a82b9921b7145e12f6da03e91122a2bb7f1"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Initial Administrator Credentials
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "sentinel_admin_password"

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
        ),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
