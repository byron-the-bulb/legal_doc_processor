from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    ENV: str = Field(default=os.getenv("ENV", "dev"))
    API_V1_STR: str = "/api/v1"

    # Dev-friendly defaults for local runs; override in .env for Docker/prod
    DATABASE_URL: str = Field(default=os.getenv("DATABASE_URL", "sqlite:///./data/dev.db"))
    REDIS_URL: str = Field(default=os.getenv("REDIS_URL", "redis://redis:6379/0"))

    BROKER_URL: str = Field(default=os.getenv("BROKER_URL", "redis://redis:6379/1"))
    CELERY_RESULT_BACKEND: str = Field(default=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2"))

    UPLOAD_DIR: str = Field(default=os.getenv("UPLOAD_DIR", "./data/uploads"))
    STORAGE_DIR: str = Field(default=os.getenv("STORAGE_DIR", "./data"))

    S3_ENDPOINT: str = Field(default=os.getenv("S3_ENDPOINT", "http://minio:9000"))
    S3_ACCESS_KEY: str = Field(default=os.getenv("S3_ACCESS_KEY", "minioadmin"))
    S3_SECRET_KEY: str = Field(default=os.getenv("S3_SECRET_KEY", "minioadmin"))
    S3_BUCKET: str = Field(default=os.getenv("S3_BUCKET", "documents"))

    # LLM configuration
    OPENAI_API_KEY: str | None = Field(default=os.getenv("OPENAI_API_KEY"))
    OPENAI_MODEL: str = Field(default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

    # PDF rendering configuration (pdf2image)
    POPPLER_PATH: str | None = Field(default=os.getenv("POPPLER_PATH"))

    # Pydantic v2 settings config
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


@lru_cache()
def get_settings() -> "Settings":
    return Settings()


settings = get_settings()
