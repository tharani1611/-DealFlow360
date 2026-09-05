import pytest
import uuid
from datetime import timedelta
from app.core.config import settings
from app.core.security import (
    hash_password,
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
    verify_access_token,
)
from app.core.exceptions import UnauthorizedException


def test_password_hashing_and_verification():
    """Verify password hashing creates distinct bcrypt hashes and verifies correctly."""
    plain_password = "SuperSecretPassword123!"

    hashed = hash_password(plain_password)
    assert hashed != plain_password
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    # Verify correct password
    assert verify_password(plain_password, hashed) is True

    # Verify incorrect password
    assert verify_password("WrongPassword!", hashed) is False

    # Verify alias function
    hashed_alias = get_password_hash(plain_password)
    assert verify_password(plain_password, hashed_alias) is True

    # Verify distinct salts for same plaintext
    hashed_second = hash_password(plain_password)
    assert hashed != hashed_second
    assert verify_password(plain_password, hashed_second) is True


def test_password_hashing_edge_cases():
    """Verify invalid and empty inputs for password functions fail safely."""
    assert verify_password("", "some_hash") is False
    assert verify_password("password", "") is False
    assert verify_password(None, "some_hash") is False
    assert verify_password("password", "invalid_hash_format") is False

    with pytest.raises(ValueError, match="cannot be empty"):
        hash_password("")


def test_jwt_create_and_decode_valid_token():
    """Verify create_access_token and decode_access_token lifecycle."""
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id)

    assert isinstance(token, str)
    assert len(token) > 20

    payload = decode_access_token(token)
    assert payload["sub"] == user_id
    assert "exp" in payload
    assert "iat" in payload

    extracted_sub = verify_access_token(token)
    assert extracted_sub == user_id


def test_jwt_expired_token_rejection():
    """Verify expired JWT access tokens raise UnauthorizedException."""
    user_id = str(uuid.uuid4())
    # Create token expired 10 seconds in the past
    expired_token = create_access_token(user_id, expires_delta=timedelta(seconds=-10))

    with pytest.raises(UnauthorizedException) as exc_info:
        decode_access_token(expired_token)
    
    assert "expired" in str(exc_info.value.message).lower() or "credentials" in str(exc_info.value.message).lower()


def test_jwt_tampered_and_malformed_token_rejection():
    """Verify tampered and malformed JWT strings are rejected."""
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id)

    # Tamper token signature
    parts = token.split(".")
    tampered_token = f"{parts[0]}.{parts[1]}.tampered_signature"

    with pytest.raises(UnauthorizedException):
        decode_access_token(tampered_token)

    # Malformed token
    with pytest.raises(UnauthorizedException):
        decode_access_token("malformed_token_string")

    with pytest.raises(UnauthorizedException):
        decode_access_token("")


def test_jwt_claims_sanitization():
    """Verify sensitive fields like password or password_hash are sanitized from JWT claims."""
    user_id = str(uuid.uuid4())
    claims = {
        "role": "Sales Rep",
        "password": "should_be_removed",
        "password_hash": "should_be_removed",
        "credit_card": "should_be_removed"
    }
    token = create_access_token(user_id, claims=claims)
    payload = decode_access_token(token)

    assert payload["sub"] == user_id
    assert payload["role"] == "Sales Rep"
    assert "password" not in payload
    assert "password_hash" not in payload
    assert "credit_card" not in payload


def test_security_configuration():
    """Verify effective security configuration parameters."""
    assert settings.effective_jwt_secret_key is not None
    assert len(settings.effective_jwt_secret_key) > 0
    assert settings.effective_jwt_algorithm in ["HS256", "HS384", "HS512"]
    assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES > 0
