import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
load_dotenv(BACKEND_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ACCESS_TOKEN_MINUTES_RAW = os.getenv("JWT_ACCESS_TOKEN_MINUTES")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is required. Set it in the process environment or "
        "in the ignored backend/.env file."
    )

if DATABASE_URL.startswith("sqlite") and os.getenv("APP_ENV") != "test":
    raise RuntimeError(
        "SQLite is allowed only for isolated automated tests. Configure "
        "DATABASE_URL for PostgreSQL."
    )

if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET is required. Set it in the process environment or "
        "in the ignored backend/.env file."
    )

if len(JWT_SECRET) < 32:
    raise RuntimeError("JWT_SECRET must contain at least 32 characters.")

if not JWT_ACCESS_TOKEN_MINUTES_RAW:
    raise RuntimeError(
        "JWT_ACCESS_TOKEN_MINUTES is required. Set it in the process "
        "environment or in the ignored backend/.env file."
    )

try:
    JWT_ACCESS_TOKEN_MINUTES = int(JWT_ACCESS_TOKEN_MINUTES_RAW)
except ValueError as error:
    raise RuntimeError("JWT_ACCESS_TOKEN_MINUTES must be an integer.") from error

if JWT_ACCESS_TOKEN_MINUTES <= 0:
    raise RuntimeError("JWT_ACCESS_TOKEN_MINUTES must be positive.")

FRONTEND_ORIGIN = os.getenv(
    "FRONTEND_ORIGIN",
    "http://localhost:5173"
)

# Keep localhost available even when an older local .env still names 127.0.0.1.
FRONTEND_ORIGINS = sorted({
    FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
})

ARTIFACT_ROOT = PROJECT_DIR.resolve()
