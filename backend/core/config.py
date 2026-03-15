"""Application configuration loaded from environment."""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@lru_cache
def get_settings():
    """Return app settings from environment (DB, CORS, secrets, OpenAI). Cached for performance."""
    return {
        "db_host": os.getenv("DB_HOST", "localhost"),
        "db_port": os.getenv("DB_PORT", "5432"),
        "db_name": os.getenv("DB_NAME", "sclapp"),
        "db_user": os.getenv("DB_USER", "postgres"),
        "db_password": os.getenv("DB_PASSWORD", "postgres"),
        "cors_origins": os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:5500").split(","),
        "secret_key": os.getenv("SECRET_KEY", "dev-secret-change-in-production"),
        "refresh_secret_key": os.getenv("REFRESH_SECRET_KEY", os.getenv("SECRET_KEY", "dev-secret-change-in-production")),
        "cookie_secure": os.getenv("COOKIE_SECURE", "false").lower() in ("1", "true", "yes"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        # Default model; job classifier always uses CLASSIFIER_MODEL in job_classifier.py
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    }
