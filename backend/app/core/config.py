import os
from urllib.parse import urlsplit
import re
from typing import List
from pydantic import model_validator
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    ENV: str = "development"
    DATABASE_URL: str = "sqlite+aiosqlite:///pagemetrics.db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT_SECONDS: float = 30.0
    DB_POOL_RECYCLE_SECONDS: int = 1800
    META_ACCESS_TOKEN: str = ""
    IG_BUSINESS_ACCOUNT_ID: str = ""
    GRAPH_API_VERSION: str = "v21.0"

    # Backup Provider Configuration
    BACKUP_ENABLED: bool = False
    BACKUP_PROVIDER: str = "serpapi"
    BACKUP_FALLBACK_ON: str = "transient,rate_limit"
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
    ]
    REEL_SAMPLE_SIZE: int = 12
    SESSION_IDLE_MINUTES: int = 30
    SESSION_ABSOLUTE_HOURS: int = 12
    INITIAL_USER: str = "agency_admin"
    INITIAL_PASSWORD: str = "SecureAgency123!"
    REFRESH_TOKEN: str = ""
    REFRESH_ALL_CONCURRENCY: int = 3
    REFRESH_WORKER_POLL_SECONDS: float = 1.0
    REFRESH_JOB_LEASE_SECONDS: int = 90
    REFRESH_JOB_RETENTION_DAYS: int = 30
    PAGE_SNAPSHOT_RETENTION_DAYS: int = 365
    PAGE_SNAPSHOT_MAX_PER_PAGE: int = 100
    PAGE_DEFAULT_SIZE: int = 50
    PAGE_MAX_SIZE: int = 200

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_postgres_database_url(cls, value):
        if not isinstance(value, str):
            return value

        url = make_url(value)
        if url.drivername in {"postgres", "postgresql"}:
            url = url.set(drivername="postgresql+asyncpg")

        if url.drivername != "postgresql+asyncpg":
            return value

        query = dict(url.query)
        sslmode = query.pop("sslmode", None)
        if sslmode is not None:
            query.setdefault("ssl", sslmode)
        query.pop("channel_binding", None)
        if "-pooler." in (url.host or ""):
            query["prepared_statement_cache_size"] = "0"

        if query != dict(url.query):
            url = url.set(query=query)
        return str(url)

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.REFRESH_ALL_CONCURRENCY < 1:
            raise ValueError("REFRESH_ALL_CONCURRENCY must be at least 1.")
        if self.DB_POOL_SIZE < 1 or self.DB_MAX_OVERFLOW < 0 or self.DB_POOL_TIMEOUT_SECONDS <= 0:
            raise ValueError("Database pool size, overflow, and timeout settings are invalid.")
        if self.PAGE_DEFAULT_SIZE < 1 or self.PAGE_MAX_SIZE < self.PAGE_DEFAULT_SIZE:
            raise ValueError("PAGE_MAX_SIZE must be greater than or equal to PAGE_DEFAULT_SIZE.")
        if self.PAGE_SNAPSHOT_RETENTION_DAYS < 1 or self.REFRESH_JOB_RETENTION_DAYS < 1:
            raise ValueError("Refresh-job and page-snapshot retention must be positive.")
        if self.PAGE_SNAPSHOT_MAX_PER_PAGE < 1:
            raise ValueError("PAGE_SNAPSHOT_MAX_PER_PAGE must be at least 1.")

        if self.ENV.lower() == "production":
            if not self.DATABASE_URL.startswith("postgresql+asyncpg://"):
                raise ValueError("Production requires PostgreSQL via postgresql+asyncpg.")
            if not self.META_ACCESS_TOKEN.strip() or not self.IG_BUSINESS_ACCOUNT_ID.strip():
                raise ValueError("Production requires META_ACCESS_TOKEN and IG_BUSINESS_ACCOUNT_ID.")
            if not self.REFRESH_TOKEN.strip():
                raise ValueError("Production requires REFRESH_TOKEN for scheduled refreshes.")
            if not self.INITIAL_USER.strip() or len(self.INITIAL_PASSWORD) < 12:
                raise ValueError("Production requires INITIAL_USER and an INITIAL_PASSWORD of at least 12 characters.")
            if self.INITIAL_USER.strip().lower() == "agency_admin" or self.INITIAL_PASSWORD == "SecureAgency123!":
                raise ValueError("Production must override the development INITIAL_USER and INITIAL_PASSWORD defaults.")
            if not re.fullmatch(r"[A-Za-z0-9._]{1,30}", self.INITIAL_USER.strip()):
                raise ValueError("INITIAL_USER must be a valid Agency ID.")
            if self.INITIAL_USER.lower() in self.INITIAL_PASSWORD.lower():
                raise ValueError("INITIAL_PASSWORD must not contain INITIAL_USER.")
            parsed_origins = [urlsplit(origin) for origin in self.CORS_ORIGINS]
            if not parsed_origins or any(
                origin.scheme != "https"
                or not origin.netloc
                or origin.path not in ("", "/")
                or origin.query
                or origin.fragment
                or origin.username
                or origin.password
                for origin in parsed_origins
            ):
                raise ValueError("Production CORS_ORIGINS must contain only HTTPS origins.")
        return self
    ARGON2_TIME_COST: int = 2
    ARGON2_MEMORY_COST: int = 65536
    ARGON2_PARALLELISM: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
