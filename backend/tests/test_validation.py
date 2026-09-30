import pytest
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
