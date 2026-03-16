"""Auth endpoints: register, login, refresh, me, logout. Tokens in HttpOnly cookies."""

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr

from backend.core.config import get_settings
from backend.core.security import (
    COOKIE_ACCESS,
    COOKIE_REFRESH,
    generate_access_token,
    generate_refresh_token,
    verify_access_token,
    verify_refresh_token,
)
from backend.db.connection import execute_query
from backend.modules.auth.auth_service import (
    AuthService,
    get_user_id_by_refresh_token,
    revoke_refresh_token,
    store_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Cookie max-age: access 15 min, refresh 7 days
ACCESS_MAX_AGE = 15 * 60
REFRESH_MAX_AGE = 7 * 24 * 60 * 60


def _cookie_params(secure: bool):
    """Common cookie options for auth cookies (HttpOnly, SameSite, path)."""
    return {
        "httponly": True,
        "samesite": "lax",
        "secure": secure,
        "path": "/",
    }


def _get_user_id_from_payload(payload: dict) -> int:
    """Extract and validate user id from JWT payload (sub claim)."""
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        return int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    settings = get_settings()
    secure = settings.get("cookie_secure", False)
    params = _cookie_params(secure)

    response.set_cookie(
        COOKIE_ACCESS,
        access_token,
        max_age=ACCESS_MAX_AGE,
        **params,
    )
    response.set_cookie(
        COOKIE_REFRESH,
        refresh_token,
        max_age=REFRESH_MAX_AGE,
        **params,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(COOKIE_ACCESS, path="/")
    response.delete_cookie(COOKIE_REFRESH, path="/")


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str


@router.post("/register")
def register(payload: RegisterRequest):
    """Register new user. No cookies."""
    data, status = AuthService.register_user(
        payload.full_name.strip(),
        payload.email,
        payload.password,
    )

    if status == 400:
        raise HTTPException(status_code=400, detail=data.get("error", "missing fields"))
    if status == 409:
        raise HTTPException(status_code=409, detail=data.get("error", "email already registered"))
    if status == 500:
        raise HTTPException(status_code=500, detail=data.get("error", "server error"))

    return data


@router.post("/login")
def login(payload: LoginRequest, response: Response):
    """Validate credentials; set access and refresh tokens in HttpOnly cookies."""
    data, status = AuthService.login_user(payload.email, payload.password)

    if status == 400:
        raise HTTPException(status_code=400, detail=data.get("error", "missing fields"))
    if status == 401:
        raise HTTPException(status_code=401, detail=data.get("error", "invalid credentials"))

    _set_auth_cookies(response, data["access_token"], data["refresh_token"])
    return {"message": data["message"], "user": data["user"]}


@router.post("/refresh")
def refresh(request: Request, response: Response):
    """Issue new access token from refresh token in cookie. Optionally rotate refresh."""
    refresh_token = request.cookies.get(COOKIE_REFRESH)

    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    try:
        payload = verify_refresh_token(refresh_token)
        user_id = _get_user_id_from_payload(payload)

        if get_user_id_by_refresh_token(refresh_token) is None:
            _clear_auth_cookies(response)
            raise HTTPException(status_code=401, detail="Refresh token revoked or expired")

        revoke_refresh_token(refresh_token)

        new_access = generate_access_token(user_id)
        new_refresh = generate_refresh_token(user_id)

        store_refresh_token(user_id, new_refresh)
        _set_auth_cookies(response, new_access, new_refresh)

        return {"message": "Token refreshed"}

    except HTTPException:
        _clear_auth_cookies(response)
        raise


@router.get("/me")
def me(request: Request):
    """Return current user from access token in cookie."""
    access_token = request.cookies.get(COOKIE_ACCESS)

    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = verify_access_token(access_token)
    user_id = _get_user_id_from_payload(payload)

    rows = execute_query(
        "SELECT id_user, full_name, email FROM users WHERE id_user = %s",
        (user_id,),
    )

    if not rows:
        raise HTTPException(status_code=401, detail="User not found")

    return {"user": dict(rows[0])}


@router.post("/logout")
def logout(request: Request, response: Response):
    """Revoke refresh token and clear auth cookies."""
    refresh_token = request.cookies.get(COOKIE_REFRESH)

    if refresh_token:
        revoke_refresh_token(refresh_token)

    _clear_auth_cookies(response)
    return {"message": "Logout successful"}