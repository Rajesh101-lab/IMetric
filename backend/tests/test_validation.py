import pytest
from pydantic import ValidationError
from app.core.config import Settings
from app.core.security import normalize_username, validate_username_format, validate_password_policy


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("instagram", "instagram"),
        (" @instagram ", "instagram"),
        ("https://instagram.com/nike/", "nike"),
        ("http://www.instagram.com/adidas?igsh=123", "adidas"),
        ("  @cristiano.ronaldo_10  ", "cristiano.ronaldo_10"),
    ]
)
def test_username_normalization(raw, expected):
    assert normalize_username(raw) == expected


@pytest.mark.parametrize(
    "username,valid",
    [
        ("nike", True),
        ("cristiano.ronaldo_10", True),
        ("a", True),
        ("a" * 30, True),
        ("a" * 31, False),  # > 30 chars
        ("user@name", False),  # invalid char @
        ("user-name", False),  # invalid char -
        ("user name", False),  # space inside
        ("<script>", False),  # HTML injection
        ("'; DROP TABLE users; --", False),  # SQL injection
    ]
)
def test_username_validation_regex(username, valid):
    assert validate_username_format(username) == valid


def test_password_policy():
    assert validate_password_policy("short", "myagency") == "Password must be at least 12 characters long."
    assert validate_password_policy("myagency12345", "myagency") is not None  # contains agency username
    assert validate_password_policy("password12345", "myagency") is not None  # common password
    assert validate_password_policy("ValidSecurePass123!", "myagency") is None


def test_production_settings_require_postgres_secrets_and_https_origins():
    base = {
        "ENV": "production",
        "DATABASE_URL": "postgresql+asyncpg://app:secret@db:5432/app",
        "INITIAL_USER": "workspace_owner",
        "INITIAL_PASSWORD": "DifferentStrongPassword2026!",
        "META_ACCESS_TOKEN": "meta-token",
        "IG_BUSINESS_ACCOUNT_ID": "12345",
        "CORS_ORIGINS": ["https://app.example.com"],
        "REFRESH_TOKEN": "some-refresh-token",
    }
    assert Settings(**base).ENV == "production"

    with pytest.raises(ValidationError, match="Production requires PostgreSQL"):
        Settings(**{**base, "DATABASE_URL": "sqlite+aiosqlite:///local.db"})

    with pytest.raises(ValidationError, match="HTTPS origins"):
        Settings(**{**base, "CORS_ORIGINS": ["http://app.example.com"]})


def test_development_settings_allow_local_sqlite():
    settings = Settings(ENV="development", DATABASE_URL="sqlite+aiosqlite:///local.db")
    assert settings.DATABASE_URL == "sqlite+aiosqlite:///local.db"


def test_postgres_url_uses_asyncpg_and_ssl():
    settings = Settings(DATABASE_URL="postgres://app:secret@db.example.com:5432/app?sslmode=require")
    assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")
    assert "ssl=require" in settings.DATABASE_URL
