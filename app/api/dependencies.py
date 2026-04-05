from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_token
from app.models.enums import UserRole, UserStatus
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def _extract_bearer_token(
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header.",
        )
    return credentials.credentials


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> User:
    token = _extract_bearer_token(credentials)
    user = db.scalar(select(User).where(User.token_hash == hash_token(token)))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )

    if user.status == UserStatus.inactive:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive users cannot access the system.",
        )

    return user


def require_roles(*allowed_roles: UserRole) -> Callable[[User], User]:
    def _role_dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            allowed = ", ".join(role.value for role in allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"User role '{current_user.role.value}' does not have access. "
                    f"Allowed roles: {allowed}."
                ),
            )
        return current_user

    return _role_dependency
