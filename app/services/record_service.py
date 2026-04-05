from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import RecordType
from app.models.financial_record import FinancialRecord
from app.schemas.record import (
    FinancialRecordCreate,
    FinancialRecordListResponse,
    FinancialRecordResponse,
    FinancialRecordUpdate,
)


def create_record(
    db: Session,
    payload: FinancialRecordCreate,
    actor_id: int,
) -> FinancialRecordResponse:
    record = FinancialRecord(
        **payload.model_dump(),
        created_by_user_id=actor_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return FinancialRecordResponse.model_validate(record)


def get_record_by_id(db: Session, record_id: int) -> FinancialRecord | None:
    return db.get(FinancialRecord, record_id)


def list_records(
    db: Session,
    *,
    record_type: RecordType | None,
    category: str | None,
    start_date: date | None,
    end_date: date | None,
    min_amount: float | None,
    max_amount: float | None,
    page: int,
    page_size: int,
) -> FinancialRecordListResponse:
    if start_date and end_date and start_date > end_date:
        raise ValueError("start_date cannot be later than end_date.")
    if (
        min_amount is not None
        and max_amount is not None
        and min_amount > max_amount
    ):
        raise ValueError("min_amount cannot be greater than max_amount.")

    query = select(FinancialRecord)

    if record_type:
        query = query.where(FinancialRecord.type == record_type)
    if category:
        query = query.where(FinancialRecord.category.ilike(f"%{category.strip()}%"))
    if start_date:
        query = query.where(FinancialRecord.date >= start_date)
    if end_date:
        query = query.where(FinancialRecord.date <= end_date)
    if min_amount is not None:
        query = query.where(FinancialRecord.amount >= min_amount)
    if max_amount is not None:
        query = query.where(FinancialRecord.amount <= max_amount)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query
        .order_by(FinancialRecord.date.desc(), FinancialRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return FinancialRecordListResponse(
        items=[FinancialRecordResponse.model_validate(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


def update_record(
    db: Session,
    record_id: int,
    payload: FinancialRecordUpdate,
) -> FinancialRecordResponse | None:
    record = db.get(FinancialRecord, record_id)
    if record is None:
        return None

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)

    db.add(record)
    db.commit()
    db.refresh(record)
    return FinancialRecordResponse.model_validate(record)


def delete_record(db: Session, record_id: int) -> bool:
    record = db.get(FinancialRecord, record_id)
    if record is None:
        return False

    db.delete(record)
    db.commit()
    return True
