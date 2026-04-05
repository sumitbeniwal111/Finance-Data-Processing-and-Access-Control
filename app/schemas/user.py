from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole, UserStatus


class UserBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    role: UserRole = UserRole.viewer
    status: UserStatus = UserStatus.active


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None
    role: UserRole | None = None
    status: UserStatus | None = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class UserCreatedResponse(BaseModel):
    user: UserResponse
    auth_token: str


class UserTokenResponse(BaseModel):
    user: UserResponse
    auth_token: str
