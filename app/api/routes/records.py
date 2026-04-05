from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.database import get_db
from app.models.enums import RecordType, UserRole
from app.models.user import User
from app.schemas.record import (
    FinancialRecordCreate,
    FinancialRecordListResponse,
    FinancialRecordResponse,
    FinancialRecordUpdate,
)
from app.services.record_service import (
    create_record,
    delete_record,
    get_record_by_id,
    list_records,
    update_record,
)

router = APIRouter(prefix="/records", tags=["Financial Records"])
record_read_access = require_roles(UserRole.analyst, UserRole.admin)
record_write_access = require_roles(UserRole.admin)


@router.post(
    "",
    response_model=FinancialRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_financial_record(
    payload: FinancialRecordCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(record_write_access)],
) -> FinancialRecordResponse:
    return create_record(db, payload, actor_id=current_user.id)


@router.get("", response_model=FinancialRecordListResponse)
def get_financial_records(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(record_read_access)],
    record_type: RecordType | None = Query(default=None, alias="type"),
    category: str | None = Query(default=None, min_length=2, max_length=100),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    min_amount: float | None = Query(default=None, gt=0),
    max_amount: float | None = Query(default=None, gt=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> FinancialRecordListResponse:
    return list_records(
        db,
        record_type=record_type,
        category=category,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        page=page,
        page_size=page_size,
    )


@router.get("/{record_id}", response_model=FinancialRecordResponse)
def get_financial_record(
    record_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(record_read_access)],
) -> FinancialRecordResponse:
    record = get_record_by_id(db, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Financial record with id {record_id} was not found.",
        )
    return record


@router.patch("/{record_id}", response_model=FinancialRecordResponse)
def update_financial_record(
    record_id: int,
    payload: FinancialRecordUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(record_write_access)],
) -> FinancialRecordResponse:
    record = update_record(db, record_id, payload)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Financial record with id {record_id} was not found.",
        )
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_financial_record(
    record_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(record_write_access)],
) -> None:
    deleted = delete_record(db, record_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Financial record with id {record_id} was not found.",
        )
