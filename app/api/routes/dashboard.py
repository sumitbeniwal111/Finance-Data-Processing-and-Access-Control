from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.dashboard import (
    CategoryTotal,
    DashboardSummaryResponse,
    RecentActivityItem,
    TrendPoint,
)
from app.services.dashboard_service import (
    build_category_totals,
    build_recent_activity,
    build_summary,
    build_trends,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
dashboard_access = require_roles(UserRole.viewer, UserRole.analyst, UserRole.admin)


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(dashboard_access)],
) -> DashboardSummaryResponse:
    return build_summary(db)


@router.get("/category-totals", response_model=list[CategoryTotal])
def get_category_totals(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(dashboard_access)],
) -> list[CategoryTotal]:
    return build_category_totals(db)


@router.get("/recent-activity", response_model=list[RecentActivityItem])
def get_recent_activity(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(dashboard_access)],
    limit: int = Query(default=5, ge=1, le=50),
) -> list[RecentActivityItem]:
    return build_recent_activity(db, limit=limit)


@router.get("/trends", response_model=list[TrendPoint])
def get_trends(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(dashboard_access)],
    months: int = Query(default=6, ge=1, le=24),
) -> list[TrendPoint]:
    return build_trends(db, months=months)
