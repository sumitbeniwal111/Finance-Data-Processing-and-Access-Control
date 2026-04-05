from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Query, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.enums import RecordType, UserRole
from app.models.user import User
from app.schemas.record import FinancialRecordCreate
from app.schemas.user import UserCreate
from app.services.dashboard_service import (
    build_category_totals,
    build_recent_activity,
    build_summary,
    build_trends,
)
from app.services.record_service import create_record, list_records
from app.services.user_service import create_user, get_user_by_token, list_users

router = APIRouter(tags=["Frontend"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
AUTH_COOKIE_NAME = "finance_access_token"


def _base_context(request: Request, current_user: User | None, **extra: object) -> dict[str, object]:
    context = {
        "request": request,
        "current_user": current_user,
        "can_view_records": current_user is not None
        and current_user.role in {UserRole.analyst, UserRole.admin},
        "can_manage_users": current_user is not None and current_user.role == UserRole.admin,
    }
    context.update(extra)
    return context


def _redirect(path: str, message: str | None = None, error: str | None = None) -> RedirectResponse:
    params: dict[str, str] = {}
    if message:
        params["message"] = message
    if error:
        params["error"] = error

    url = path if not params else f"{path}?{urlencode(params)}"
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


def get_frontend_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        return None
    return get_user_by_token(db, token)


def _ensure_frontend_user(current_user: User | None) -> RedirectResponse | None:
    if current_user is None:
        return _redirect("/app", error="Please sign in with a valid token first.")
    return None


def _ensure_record_access(current_user: User | None) -> RedirectResponse | None:
    user_redirect = _ensure_frontend_user(current_user)
    if user_redirect is not None:
        return user_redirect
    if current_user.role not in {UserRole.analyst, UserRole.admin}:
        return _redirect("/app/dashboard", error="Your role can view the dashboard, but not records.")
    return None


def _ensure_admin_access(current_user: User | None) -> RedirectResponse | None:
    user_redirect = _ensure_frontend_user(current_user)
    if user_redirect is not None:
        return user_redirect
    if current_user.role != UserRole.admin:
        return _redirect("/app/dashboard", error="This page is available only for admin users.")
    return None


def _safe_decimal(value: str) -> Decimal:
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Amount must be a valid decimal number.") from exc


@router.get("/app")
def frontend_home(
    request: Request,
    current_user: Annotated[User | None, Depends(get_frontend_user)],
    message: str | None = Query(default=None),
    error: str | None = Query(default=None),
):
    if current_user is not None:
        return _redirect("/app/dashboard")
    return templates.TemplateResponse(
        request,
        "login.html",
        _base_context(request, current_user, message=message, error=error),
    )


@router.post("/app/login")
def frontend_login(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    token: str = Form(...),
):
    user = get_user_by_token(db, token.strip())
    if user is None:
        return templates.TemplateResponse(
            request,
            "login.html",
            _base_context(
                request,
                None,
                error="Invalid token. Use one of the seeded demo tokens or an admin-generated token.",
            ),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    response = _redirect("/app/dashboard", message=f"Signed in as {user.full_name}.")
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token.strip(),
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/app/logout")
def frontend_logout():
    response = _redirect("/app", message="You have been signed out.")
    response.delete_cookie(AUTH_COOKIE_NAME)
    return response


@router.get("/app/dashboard")
def dashboard_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_frontend_user)],
    message: str | None = Query(default=None),
):
    redirect = _ensure_frontend_user(current_user)
    if redirect is not None:
        return redirect
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        _base_context(
            request,
            current_user,
            message=message,
            summary=build_summary(db),
            category_totals=build_category_totals(db),
            recent_activity=build_recent_activity(db, limit=6),
            trends=build_trends(db, months=6),
        ),
    )


@router.get("/app/records")
def records_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_frontend_user)],
    message: str | None = Query(default=None),
    error: str | None = Query(default=None),
    record_type: RecordType | None = Query(default=None, alias="type"),
    category: str | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    min_amount: float | None = Query(default=None),
    max_amount: float | None = Query(default=None),
):
    redirect = _ensure_record_access(current_user)
    if redirect is not None:
        return redirect
    try:
        records = list_records(
            db,
            record_type=record_type,
            category=category,
            start_date=start_date,
            end_date=end_date,
            min_amount=min_amount,
            max_amount=max_amount,
            page=1,
            page_size=100,
        )
    except ValueError as exc:
        return _redirect("/app/records", error=str(exc))
    return templates.TemplateResponse(
        request,
        "records.html",
        _base_context(
            request,
            current_user,
            message=message,
            error=error,
            filters={
                "type": record_type.value if record_type else "",
                "category": category or "",
                "start_date": start_date.isoformat() if start_date else "",
                "end_date": end_date.isoformat() if end_date else "",
                "min_amount": "" if min_amount is None else min_amount,
                "max_amount": "" if max_amount is None else max_amount,
            },
            records=records,
            record_types=list(RecordType),
        ),
    )


@router.post("/app/records")
def create_record_page(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_frontend_user)],
    amount: str = Form(...),
    record_type: RecordType = Form(..., alias="type"),
    category: str = Form(...),
    record_date: date = Form(..., alias="date"),
    notes: str = Form(default=""),
):
    redirect = _ensure_admin_access(current_user)
    if redirect is not None:
        return redirect
    try:
        payload = FinancialRecordCreate(
            amount=_safe_decimal(amount),
            type=record_type,
            category=category,
            date=record_date,
            notes=notes or None,
        )
        create_record(db, payload, actor_id=current_user.id)
    except ValueError as exc:
        return _redirect("/app/records", error=str(exc))
    return _redirect("/app/records", message="Financial record created successfully.")


@router.get("/app/users")
def users_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_frontend_user)],
    message: str | None = Query(default=None),
    error: str | None = Query(default=None),
):
    redirect = _ensure_admin_access(current_user)
    if redirect is not None:
        return redirect
    return templates.TemplateResponse(
        request,
        "users.html",
        _base_context(
            request,
            current_user,
            message=message,
            error=error,
            users=list_users(db),
            roles=list(UserRole),
        ),
    )


@router.post("/app/users")
def create_user_page(
    current_user: Annotated[User | None, Depends(get_frontend_user)],
    db: Annotated[Session, Depends(get_db)],
    full_name: str = Form(...),
    email: str = Form(...),
    role: UserRole = Form(...),
):
    redirect = _ensure_admin_access(current_user)
    if redirect is not None:
        return redirect
    try:
        payload = UserCreate(
            full_name=full_name,
            email=email,
            role=role,
        )
        create_user(db, payload)
    except ValueError as exc:
        return _redirect("/app/users", error=str(exc))
    return _redirect("/app/users", message="User created successfully.")
