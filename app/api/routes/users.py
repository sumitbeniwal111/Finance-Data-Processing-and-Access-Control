from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_roles
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserCreatedResponse,
    UserResponse,
    UserTokenResponse,
    UserUpdate,
)
from app.services.user_service import (
    create_user,
    get_user_by_id,
    list_users,
    rotate_user_token,
    seed_demo_users,
    update_user,
)

router = APIRouter(prefix="/users", tags=["Users"])
admin_only = require_roles(UserRole.admin)


@router.post("", response_model=UserCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_new_user(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(admin_only)],
) -> UserCreatedResponse:
    user, raw_token = create_user(db, payload)
    return UserCreatedResponse(user=user, auth_token=raw_token)


@router.get("", response_model=list[UserResponse])
def get_users(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(admin_only)],
) -> list[UserResponse]:
    return list_users(db)


@router.post("/seed/demo", response_model=list[UserTokenResponse], status_code=status.HTTP_201_CREATED)
def create_demo_users(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(admin_only)],
) -> list[UserTokenResponse]:
    seeded = seed_demo_users(db)
    return [UserTokenResponse(user=user, auth_token=token) for user, token in seeded]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    if current_user.role != UserRole.admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own user profile.",
        )

    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} was not found.",
        )
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_existing_user(
    user_id: int,
    payload: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(admin_only)],
) -> UserResponse:
    user = update_user(db, user_id, payload)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} was not found.",
        )
    return user


@router.post("/{user_id}/rotate-token", response_model=UserTokenResponse)
def rotate_token(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(admin_only)],
) -> UserTokenResponse:
    user, raw_token = rotate_user_token(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} was not found.",
        )
    return UserTokenResponse(user=user, auth_token=raw_token)
