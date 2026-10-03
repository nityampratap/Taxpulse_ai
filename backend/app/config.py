from decimal import Decimal
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "TAXPULSE AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database: Default to SQLite fallback per AGENTS.md
    DATABASE_URL: str = "sqlite:///./taxpulse.db"
    SQLITE_FALLBACK_URL: str = "sqlite:///./taxpulse.db"

    # CORS
    FRONTEND_ORIGIN: Union[str, List[str]] = "http://localhost:5173"
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    # Security
    SECRET_KEY: str = "change-this-to-a-secure-random-32-byte-hex-in-production"
    JWT_SECRET: str = ""
    JWT_EXPIRE_MINUTES: int = 60

    # AI providers
    AI_PROVIDER_ORDER: str = "groq,gemini,mock"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = ""
    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = ""
    EMBEDDER: str = "tfidf"

    # WhatsApp
    WHATSAPP_MODE: str = "DEMO"
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_APP_SECRET: str = ""

    # Storage
    STORAGE_PROVIDER: str = "local"
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_BUCKET: str = "taxpulse-files"

    # Reconciliation tolerances
    TOLERANCE_AMOUNT_INR: Decimal = Decimal("1.00")
    TOLERANCE_AMOUNT_PERCENT: Decimal = Decimal("0.0001")  # 0.01%
    TOLERANCE_DATE_DAYS: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", "FRONTEND_ORIGIN", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return [str(i).strip() for i in v if str(i).strip()]
        return ["http://localhost:5173"]


settings = Settings()
