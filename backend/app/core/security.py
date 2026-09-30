import hashlib
import re
import secrets
from typing import Optional
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from app.core.config import settings

ph = PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST,
    parallelism=settings.ARGON2_PARALLELISM,
)

TOP_COMMON_PASSWORDS = {
    "password", "password123", "123456789012", "admin1234567", "welcome12345",
    "letmein12345", "changeme1234", "qwertyuiop12", "iloveyou1234", "agency123456"
}

DUMMY_HASH = ph.hash("dummy_password_for_timing_safety_123456789")


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def dummy_verify_password() -> None:
    try:
        ph.verify(DUMMY_HASH, "dummy_password_for_timing_safety_123456789")
    except Exception:
        pass


def validate_password_policy(password: str, username: str) -> Optional[str]:
    """
    Enforces password rules:
    - Minimum 12 characters
    - Maximum 128 characters
    - Must not contain or equal username
    - Must not contain top common passwords
    """
    if len(password) < 12:
        return "Password must be at least 12 characters long."
    if len(password) > 128:
        return "Password must not exceed 128 characters."
    if username and username.lower() in password.lower():
        return "Password cannot contain or match your Agency ID."
    if any(common in password.lower() for common in TOP_COMMON_PASSWORDS):
        return "Password contains a top common password pattern."
    return None


def generate_opaque_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def verify_csrf_token(cookie_token: Optional[str], header_token: Optional[str]) -> bool:
    if not cookie_token or not header_token:
        return False
    return secrets.compare_digest(cookie_token, header_token)


def normalize_username(input_val: str) -> str:
    cleaned = input_val.strip()
    if cleaned.startswith("@"):
        cleaned = cleaned[1:].strip()

    url_pattern = r"(?:https?://)?(?:www\.)?instagram\.com/([A-Za-z0-9._]{1,30})"
    match = re.search(url_pattern, cleaned, re.IGNORECASE)
    if match:
        cleaned = match.group(1)

    return cleaned.lower()


def validate_username_format(username: str) -> bool:
    return bool(re.match(r"^[A-Za-z0-9._]{1,30}$", username))
