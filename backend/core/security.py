"""JWT tokens (access + refresh) and cookie helpers. No Bearer header; cookies only."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from fastapi import HTTPException, Request

from backend.core.config import get_settings
from backend.db.connection import execute_query

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

COOKIE_ACCESS = "sclapp_access_token"
COOKIE_REFRESH = "sclapp_refresh_token"


def _secret() -> str:
    return get_settings()["secret_key"]


def _refresh_secret() -> str:
    return get_settings()["refresh_secret_key"]


def _get_user_id_from_payload(payload: Dict[str, Any]) -> int:
    """Extract and validate user id from JWT payload."""
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        return int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")


def generate_access_token(user_id: int) -> str:
    """Short-lived JWT for API auth (e.g. 15 min)."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, settings["secret_key"], algorithm=ALGORITHM)


def generate_refresh_token(user_id: int) -> str:
    """Long-lived JWT for refreshing access (e.g. 7 days)."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, settings["refresh_secret_key"], algorithm=ALGORITHM)


def verify_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate access token. Raises HTTPException 401 on failure."""
    try:
        payload = jwt.decode(token, _secret(), algorithms=[ALGORITHM])

        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")

        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def verify_refresh_token(token: str) -> Dict[str, Any]:
    """Decode and validate refresh token. Raises HTTPException 401 on failure."""
    try:
        payload = jwt.decode(token, _refresh_secret(), algorithms=[ALGORITHM])

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


def get_current_user_from_cookie(request: Request) -> Dict[str, Any]:
    """Dependency: return current user from access token cookie. Raises 401 if missing/invalid."""
    token = request.cookies.get(COOKIE_ACCESS)

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = verify_access_token(token)
    user_id = _get_user_id_from_payload(payload)

    rows = execute_query(
        "SELECT id_user, full_name, email, user_name, profile_picture FROM users WHERE id_user = %s",
        (user_id,),
    )

    if not rows:
        raise HTTPException(status_code=401, detail="User not found")

    return dict(rows[0])