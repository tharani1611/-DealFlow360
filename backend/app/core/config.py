import json
from typing import List, Union, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    APP_NAME: str = "DealFlow360"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "DEFAULT_UNSECURE_DEVELOPMENT_SECRET_KEY_MUST_BE_REPLACED"

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "dealflow_user"
    POSTGRES_PASSWORD: str = "dealflow_password"
    POSTGRES_DB: str = "dealflow360"
    DATABASE_URL: str = "postgresql+asyncpg://dealflow_user:dealflow_password@localhost:5432/dealflow360"

    # JWT Security Configuration
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Backwards compatibility / alias fallbacks
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ALGORITHM: str = "HS256"
    LOG_LEVEL: str = "INFO"

    # AI Intelligence Configuration
    AI_ENABLED: bool = True
    AI_PROVIDER: str = "gemini"  # "gemini" or "mock"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    AI_MAX_OUTPUT_TOKENS: int = 1000
    AI_TEMPERATURE: float = 0.2
    AI_TIMEOUT_SECONDS: float = 15.0

    @property
    def effective_jwt_secret_key(self) -> str:
        """Returns JWT_SECRET_KEY if configured, falling back to SECRET_KEY."""
        return self.JWT_SECRET_KEY or self.SECRET_KEY

    @property
    def effective_jwt_algorithm(self) -> str:
        """Returns JWT_ALGORITHM."""
        return self.JWT_ALGORITHM or self.ALGORITHM

    @field_validator("CORS_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_json_list(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v


settings = Settings()
