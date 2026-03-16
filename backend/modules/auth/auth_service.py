"""Auth service: register, login with werkzeug; refresh token storage and revocation."""

import hashlib
import re
from datetime import datetime, timedelta, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from backend.core.security import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    generate_access_token,
    generate_refresh_token,
)
from backend.db.connection import execute_query


def _sanitize_username(email: str) -> str:
    """Build a safe user_name from email (part before @), alphanumeric only."""
    base = email.split("@")[0] if "@" in email else email
    base = re.sub(r"[^a-zA-Z0-9_]", "", base) or "user"
    return base[:50]


def _hash_refresh_token(token: str) -> str:
    """Return SHA-256 hex digest of the token for storage (never store plain refresh token)."""
    return hashlib.sha256(token.encode()).hexdigest()


def store_refresh_token(id_user: int, refresh_token: str) -> None:
    """Save hashed refresh token in refresh_tokens for later validation and revocation."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    token_hash = _hash_refresh_token(refresh_token)

    execute_query(
        """
        INSERT INTO refresh_tokens (id_user, token_hash, expires_at)
        VALUES (%s, %s, %s)
        """,
        (id_user, token_hash, expires_at),
        fetch=False,
    )


def revoke_refresh_token(refresh_token: str) -> None:
    """Mark the refresh token as revoked so it can no longer be used."""
    token_hash = _hash_refresh_token(refresh_token)

    execute_query(
        """
        UPDATE refresh_tokens
        SET revoked_at = CURRENT_TIMESTAMP
        WHERE token_hash = %s AND revoked_at IS NULL
        """,
        (token_hash,),
        fetch=False,
    )


def get_user_id_by_refresh_token(refresh_token: str) -> int | None:
    """Return id_user if token exists, is not revoked, and is not expired."""
    token_hash = _hash_refresh_token(refresh_token)

    rows = execute_query(
        """
        SELECT id_user
        FROM refresh_tokens
        WHERE token_hash = %s
          AND revoked_at IS NULL
          AND expires_at > CURRENT_TIMESTAMP
        """,
        (token_hash,),
    )

    if not rows:
        return None

    return int(rows[0]["id_user"])


class AuthService:
    """Handles user registration and login; returns (data_dict, status_code)."""

    @staticmethod
    def register_user(full_name: str, email: str, password: str):
        """
        Create a new user. Checks email uniqueness and assigns default role.
        Returns ({"message": ...}, 201) or ({"error": ...}, 4xx/5xx).
        """
        if not (full_name and email and password):
            return {"error": "missing fields"}, 400

        full_name = full_name.strip()
        email = email.strip().lower()

        if "@" not in email:
            return {"error": "invalid email"}, 400

        existing = execute_query(
            "SELECT id_user FROM users WHERE LOWER(email) = %s",
            (email,),
        )
        if existing:
            return {"error": "email already registered"}, 409

        user_name_base = _sanitize_username(email)
        user_name = user_name_base
        suffix = 0

        while execute_query(
            "SELECT id_user FROM users WHERE user_name = %s",
            (user_name,),
        ):
            suffix += 1
            user_name = f"{user_name_base}{suffix}"

        role_row = execute_query(
            "SELECT id_role FROM public.role WHERE code = %s LIMIT 1",
            ("user",),
        )
        if not role_row:
            return {"error": "default role not found"}, 500

        id_role = role_row[0]["id_role"]
        doc_num = email
        password_hash = generate_password_hash(password)

        execute_query(
            """
            INSERT INTO users (full_name, doc_num, user_name, email, password_hash, id_role)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (full_name, doc_num, user_name, email, password_hash, id_role),
            fetch=False,
        )

        return {"message": "User registered successfully"}, 201

    @staticmethod
    def login_user(email: str, password: str):
        """
        Validate credentials and return user + tokens. Stores refresh token hash in DB.
        Returns ({"message", "user", "access_token", "refresh_token"}, 200) or ({"error": ...}, 4xx).
        """
        if not email or not password:
            return {"error": "missing fields"}, 400

        email = email.strip().lower()

        rows = execute_query(
            """
            SELECT id_user, full_name, email, password_hash
            FROM users
            WHERE LOWER(email) = %s
            """,
            (email,),
        )

        if not rows:
            return {"error": "invalid credentials"}, 401

        user = rows[0]

        if not check_password_hash(user["password_hash"], password):
            return {"error": "invalid credentials"}, 401

        user_id = int(user["id_user"])

        execute_query(
            "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id_user = %s",
            (user_id,),
            fetch=False,
        )

        access_token = generate_access_token(user_id)
        refresh_token = generate_refresh_token(user_id)
        store_refresh_token(user_id, refresh_token)

        return {
            "message": "Login successful",
            "user": {
                "id_user": user_id,
                "full_name": user["full_name"],
                "email": user["email"],
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
        }, 200