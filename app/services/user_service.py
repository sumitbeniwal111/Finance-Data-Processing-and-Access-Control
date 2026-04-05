from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import generate_token, hash_token
from app.models.enums import UserRole, UserStatus
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

settings = get_settings()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _email_exists(db: Session, email: str, *, exclude_user_id: int | None = None) -> bool:
    query = select(func.count(User.id)).where(User.email == _normalize_email(email))
    if exclude_user_id is not None:
        query = query.where(User.id != exclude_user_id)
    return bool(db.scalar(query))


def create_user(db: Session, payload: UserCreate) -> tuple[User, str]:
    normalized_email = _normalize_email(payload.email)
    if _email_exists(db, normalized_email):
        raise ValueError(f"User with email '{normalized_email}' already exists.")

    raw_token = generate_token()
    user = User(
        full_name=payload.full_name.strip(),
        email=normalized_email,
        role=payload.role,
        status=payload.status,
        token_hash=hash_token(raw_token),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, raw_token


def list_users(db: Session) -> list[User]:
    return db.scalars(select(User).order_by(User.created_at.asc(), User.id.asc())).all()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_token(db: Session, token: str) -> User | None:
    return db.scalar(select(User).where(User.token_hash == hash_token(token)))


def update_user(db: Session, user_id: int, payload: UserUpdate) -> User | None:
    user = db.get(User, user_id)
    if user is None:
        return None

    updates = payload.model_dump(exclude_unset=True)
    if "email" in updates:
        normalized_email = _normalize_email(updates["email"])
        if _email_exists(db, normalized_email, exclude_user_id=user_id):
            raise ValueError(f"User with email '{normalized_email}' already exists.")
        updates["email"] = normalized_email

    if "full_name" in updates and updates["full_name"] is not None:
        updates["full_name"] = updates["full_name"].strip()

    for field, value in updates.items():
        setattr(user, field, value)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def rotate_user_token(db: Session, user_id: int) -> tuple[User | None, str | None]:
    user = db.get(User, user_id)
    if user is None:
        return None, None

    raw_token = generate_token()
    user.token_hash = hash_token(raw_token)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, raw_token


def ensure_bootstrap_admin(db: Session) -> tuple[User, str] | None:
    existing_admin = db.scalar(select(User).where(User.role == UserRole.admin))
    if existing_admin is not None:
        return None

    admin = User(
        full_name=settings.bootstrap_admin_name,
        email=_normalize_email(settings.bootstrap_admin_email),
        role=UserRole.admin,
        status=UserStatus.active,
        token_hash=hash_token(settings.bootstrap_admin_token),
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin, settings.bootstrap_admin_token


def seed_demo_users(db: Session) -> list[tuple[User, str]]:
    defaults = [
        {
            "full_name": "Finance Analyst",
            "email": "analyst@example.com",
            "role": UserRole.analyst,
            "status": UserStatus.active,
            "token": "analyst-demo-token",
        },
        {
            "full_name": "Dashboard Viewer",
            "email": "viewer@example.com",
            "role": UserRole.viewer,
            "status": UserStatus.active,
            "token": "viewer-demo-token",
        },
    ]
    created: list[tuple[User, str]] = []

    for item in defaults:
        existing = db.scalar(select(User).where(User.email == item["email"]))
        if existing is not None:
            continue

        user = User(
            full_name=item["full_name"],
            email=item["email"],
            role=item["role"],
            status=item["status"],
            token_hash=hash_token(item["token"]),
        )
        db.add(user)
        db.flush()
        created.append((user, item["token"]))

    if created:
        db.commit()
        for user, _ in created:
            db.refresh(user)

    return created
