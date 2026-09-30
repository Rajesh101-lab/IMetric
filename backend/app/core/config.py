import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "development"
    DATABASE_URL: str = "sqlite+aiosqlite:///pagemetrics.db"
    META_ACCESS_TOKEN: str = ""
    IG_BUSINESS_ACCOUNT_ID: str = ""
    GRAPH_API_VERSION: str = "v21.0"

    # Backup Provider Configuration
    BACKUP_ENABLED: bool = False
    BACKUP_PROVIDER: str = "serpapi"
    BACKUP_FALLBACK_ON: str = "not_found,transient,rate_limit,auth,permission"
    BACKUP_DAILY_LIMIT: int = 200
    BACKUP_PER_AGENCY_DAILY_LIMIT: int = 50
    SERPAPI_API_KEY: str = ""

    IG_CONNECT_TIMEOUT: float = 5.0
    IG_READ_TIMEOUT: float = 20.0
    IG_WRITE_TIMEOUT: float = 10.0
    IG_POOL_TIMEOUT: float = 5.0
    IG_OVERALL_TIMEOUT: float = 45.0

    IG_CONCURRENCY_LIMIT: int = 3
    CIRCUIT_BREAKER_FAILURES: int = 5
    CIRCUIT_BREAKER_RESET_SECONDS: float = 60.0
    NEGATIVE_CACHE_TTL_SECONDS: float = 300.0

    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://10.0.2.2:8000",
        "http://10.0.2.2:5173",
    ]
    REEL_SAMPLE_SIZE: int = 12
    SESSION_IDLE_MINUTES: int = 30
    SESSION_ABSOLUTE_HOURS: int = 12
    INITIAL_USER: str = "agency_admin"
    INITIAL_PASSWORD: str = "SecureAgency123!"
    REFRESH_ALL_CONCURRENCY: int = 3
    ARGON2_TIME_COST: int = 2
    ARGON2_MEMORY_COST: int = 65536
    ARGON2_PARALLELISM: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
