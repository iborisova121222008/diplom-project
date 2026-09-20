from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import JWT_ACCESS_TOKEN_MINUTES, JWT_SECRET
from app.database import get_session
from app.models import User


JWT_ALGORITHM = "HS256"
PASSWORD_HASH = PasswordHash.recommended()
BEARER_SCHEME = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return PASSWORD_HASH.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return PASSWORD_HASH.verify(password, password_hash)


def create_access_token(researcher_id: str) -> str:
    issued_at = datetime.now(timezone.utc)
    payload = {
        "sub": researcher_id,
        "iat": issued_at,
        "exp": issued_at + timedelta(minutes=JWT_ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Необходима е валидна автентикация.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_researcher(
    credentials: HTTPAuthorizationCredentials | None = Security(BEARER_SCHEME),
    session: Session = Depends(get_session),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise authentication_error()

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "exp"]},
        )
        researcher_id = payload.get("sub")
        if not isinstance(researcher_id, str) or not researcher_id:
            raise authentication_error()
    except InvalidTokenError as error:
        raise authentication_error() from error

    user = session.scalar(
        select(User).where(User.researcher_id == researcher_id)
    )
    if user is None:
        raise authentication_error()
    return user
