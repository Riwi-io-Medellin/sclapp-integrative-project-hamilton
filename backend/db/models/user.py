"""User model and response schema (maps to `users` table)."""

from pydantic import BaseModel


class UserResponse(BaseModel):
    id_user: int
    full_name: str | None
    email: str
    user_name: str
    profile_picture: str | None = None

    class Config:
        from_attributes = True
