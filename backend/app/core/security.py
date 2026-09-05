import uuid
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Union, Dict
from jose import jwt, JWTError
from app.core.config import settings
from app.core.exceptions import UnauthorizedException


def hash_password(password: str) -> str:
    """Generates a secure bcrypt password hash for user credential storage."""
    if not password:
        raise ValueError("Password cannot be empty")
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def get_password_hash(password: str) -> str:
    """Alias for hash_password for backwards compatibility."""
    return hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a stored bcrypt hash safely."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(
    subject: Union[str, uuid.UUID],
    expires_delta: Optional[timedelta] = None,
    claims: Optional[Dict[str, Any]] = None
) -> str:
    """Creates a signed JWT access token containing subject (user UUID) and UTC expiration."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }

    if claims:
        # Filter out forbidden sensitive claims if accidentally provided
        forbidden_keys = {"password", "password_hash", "secret", "email", "credit_card"}
        filtered_claims = {k: v for k, v in claims.items() if k not in forbidden_keys}
        payload.update(filtered_claims)

    secret = settings.effective_jwt_secret_key
    algorithm = settings.effective_jwt_algorithm

    encoded_jwt = jwt.encode(payload, secret, algorithm=algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT access token, enforcing signature and expiration."""
    if not token or not isinstance(token, str):
        raise UnauthorizedException("Invalid authentication token")

    secret = settings.effective_jwt_secret_key
    algorithm = settings.effective_jwt_algorithm

    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        subject: Optional[str] = payload.get("sub")
        if not subject:
            raise UnauthorizedException("Token payload is missing subject claim")
        return payload
    except JWTError as exc:
        raise UnauthorizedException(f"Could not validate credentials: {str(exc)}")


def verify_access_token(token: str) -> str:
    """Validates JWT access token and returns the authenticated user subject ID."""
    payload = decode_access_token(token)
    subject = payload.get("sub")
    if not subject:
        raise UnauthorizedException("Token missing subject")
    return subject
