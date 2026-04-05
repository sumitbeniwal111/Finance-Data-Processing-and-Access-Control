from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import RecordType


class DashboardSummaryResponse(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_balance: Decimal
    total_records: int


class CategoryTotal(BaseModel):
    category: str
    type: RecordType
    total: Decimal


class TrendPoint(BaseModel):
    period: str
    income: Decimal
    expense: Decimal
    net: Decimal


class RecentActivityItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    type: RecordType
    category: str
    date: date
    notes: str | None
    created_by_user_id: int
    created_at: datetime
