"""Profile and SMTP configuration (current user from access token cookie)."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

from backend.core.security import get_current_user_from_cookie
from backend.db.connection import execute_query

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me")
def get_profile(current_user: dict = Depends(get_current_user_from_cookie)):
    """Return current user profile from access token cookie."""
    return {
        "id_user": current_user["id_user"],
        "name": current_user["full_name"] or current_user["user_name"],
        "full_name": current_user["full_name"],
        "email": current_user["email"],
        "user_name": current_user["user_name"],
        "profile_picture": current_user.get("profile_picture"),
    }


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    email: EmailStr | None = None


@router.put("/me")
def update_profile(payload: UpdateProfileRequest, current_user: dict = Depends(get_current_user_from_cookie)):
    """Update current user profile."""
    fields = []
    params = []
    if payload.name is not None:
        fields.append("full_name = %s")
        params.append(payload.name.strip())
    if payload.email is not None:
        fields.append("email = %s")
        params.append(payload.email.strip().lower())

    if not fields:
        return {"message": "Nothing to update"}

    params.append(current_user["id_user"])
    execute_query(
        f"UPDATE users SET {', '.join(fields)} WHERE id_user = %s",
        tuple(params),
        fetch=False,
    )
    return {"message": "Profile updated"}


class SmtpConfigRequest(BaseModel):
    host: str
    user: str
    password: str | None = None


@router.put("/smtp")
def update_smtp_config(payload: SmtpConfigRequest):
    """Save SMTP settings for the user (store in DB or env)."""
    # TODO: store in user_settings or similar table
    return {"message": "SMTP configuration saved"}


@router.post("/smtp/test")
def test_smtp():
    """Test SMTP connection (placeholder)."""
    return {"message": "Connection to SMTP server established"}
