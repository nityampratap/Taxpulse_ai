"""JWT authentication + bcrypt password hashing + RBAC."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.models.models import User

ALGORITHM = "HS256"
_bearer = HTTPBearer(auto_error=False)

ROLES = {"ADMIN", "ACCOUNTANT", "REVIEWER", "VIEWER"}

# Role hierarchy: higher index = more privilege
ROLE_HIERARCHY = {"VIEWER": 0, "ACCOUNTANT": 1, "REVIEWER": 2, "ADMIN": 3}


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user: User) -> str:
    expire_minutes = getattr(settings, "JWT_EXPIRE_MINUTES", 60)
    secret = getattr(settings, "JWT_SECRET", settings.SECRET_KEY)
    payload = {
        "sub": user.id,
        "org": user.organization_id,
        "role": user.role,
        "email": user.email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=int(expire_minutes)),
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    secret = getattr(settings, "JWT_SECRET", settings.SECRET_KEY)
    try:
        return jwt.decode(token, secret, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header")
    payload = decode_token(credentials.credentials)
    user = db.query(User).filter_by(id=payload["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


class RequireRole:
    """FastAPI dependency that checks the user has at least the given role."""

    def __init__(self, min_role: str):
        self.min_level = ROLE_HIERARCHY.get(min_role, 0)

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        user_level = ROLE_HIERARCHY.get(user.role, 0)
        if user_level < self.min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role {list(ROLE_HIERARCHY.keys())[self.min_level]} or higher",
            )
        return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter_by(email=email, is_active=True).first()
    if not user or not user.password_hash:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
