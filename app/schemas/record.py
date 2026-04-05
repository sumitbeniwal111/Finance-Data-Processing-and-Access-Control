from datetime import date as date_type, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, condecimal

from app.models.enums import RecordType


MoneyField = condecimal(gt=0, max_digits=12, decimal_places=2)


class FinancialRecordBase(BaseModel):
    amount: MoneyField
    type: RecordType
    category: str = Field(min_length=2, max_length=100)
    date: date_type
    notes: str | None = Field(default=None, max_length=500)


class FinancialRecordCreate(FinancialRecordBase):
    pass


class FinancialRecordUpdate(BaseModel):
    amount: MoneyField | None = None
    type: RecordType | None = None
    category: str | None = Field(default=None, min_length=2, max_length=100)
    date: date_type | None = None
    notes: str | None = Field(default=None, max_length=500)


class FinancialRecordResponse(FinancialRecordBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime


class FinancialRecordListResponse(BaseModel):
    items: list[FinancialRecordResponse]
    total: int
    page: int
    page_size: int
