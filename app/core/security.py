import logging
import os
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User

try:
    # Loads variables from a local .env file during development (no-op if absent)
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Bearer scheme for Swagger UI and API headers
security_scheme = HTTPBearer()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))  # default 24 hours

MIN_SECRET_LENGTH = 32
_WEAK_SECRETS = {
    "secret",
    "changeme",
    "change-me",
    "your-secret-key",
    "supersecret",
    "##eldorsketch##",  # the old hard-coded value is compromised; never accept it
}


def _is_production() -> bool:
    env = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development")).lower()
    return env in {"production", "prod"}


def _load_secret_key() -> str:
    key = os.getenv("JWT_SECRET_KEY")

    if _is_production():
        if not key:
            raise RuntimeError("JWT_SECRET_KEY must be set in production.")
        if len(key) < MIN_SECRET_LENGTH or key.lower() in _WEAK_SECRETS:
            raise RuntimeError(
                f"JWT_SECRET_KEY is too weak. Use a random value of at least "
                f"{MIN_SECRET_LENGTH} characters."
            )
        return key

    # Development / testing
    if key:
        if len(key) < MIN_SECRET_LENGTH or key.lower() in _WEAK_SECRETS:
            logger.warning("JWT_SECRET_KEY is weak. This is tolerated outside production only.")
        return key

    logger.warning(
        "JWT_SECRET_KEY not set; using a temporary random key. "
        "Tokens will be invalidated on every restart."
    )
    return secrets.token_urlsafe(64)


SECRET_KEY = _load_secret_key()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(credentials.credentials)
    if payload is None or payload.get("purpose"):  # reject reset tokens
        raise credentials_exception

    email: Optional[str] = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        raise credentials_exception

    return user