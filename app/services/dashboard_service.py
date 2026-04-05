from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.enums import RecordType
from app.models.financial_record import FinancialRecord
from app.schemas.dashboard import (
    CategoryTotal,
    DashboardSummaryResponse,
    RecentActivityItem,
    TrendPoint,
)


def _decimal(value: Decimal | int | float | None) -> Decimal:
    return Decimal(value or 0).quantize(Decimal("0.01"))


def _period_expression(db: Session):
    dialect = db.bind.dialect.name if db.bind else ""
    if dialect == "sqlite":
        return func.strftime("%Y-%m", FinancialRecord.date)
    if dialect == "mysql":
        return func.date_format(FinancialRecord.date, "%Y-%m")
    return func.to_char(FinancialRecord.date, "YYYY-MM")


def build_summary(db: Session) -> DashboardSummaryResponse:
    income_sum = func.coalesce(
        func.sum(
            case(
                (FinancialRecord.type == RecordType.income, FinancialRecord.amount),
                else_=0,
            )
        ),
        0,
    )
    expense_sum = func.coalesce(
        func.sum(
            case(
                (FinancialRecord.type == RecordType.expense, FinancialRecord.amount),
                else_=0,
            )
        ),
        0,
    )

    totals = db.execute(
        select(
            income_sum.label("total_income"),
            expense_sum.label("total_expenses"),
            func.count(FinancialRecord.id).label("total_records"),
        )
    ).one()

    total_income = _decimal(totals.total_income)
    total_expenses = _decimal(totals.total_expenses)
    return DashboardSummaryResponse(
        total_income=total_income,
        total_expenses=total_expenses,
        net_balance=(total_income - total_expenses).quantize(Decimal("0.01")),
        total_records=totals.total_records,
    )


def build_category_totals(db: Session) -> list[CategoryTotal]:
    rows = db.execute(
        select(
            FinancialRecord.category,
            FinancialRecord.type,
            func.sum(FinancialRecord.amount).label("total"),
        )
        .group_by(FinancialRecord.category, FinancialRecord.type)
        .order_by(FinancialRecord.category.asc())
    ).all()

    return [
        CategoryTotal(
            category=row.category,
            type=row.type,
            total=_decimal(row.total),
        )
        for row in rows
    ]


def build_recent_activity(db: Session, limit: int = 5) -> list[RecentActivityItem]:
    rows = db.scalars(
        select(FinancialRecord)
        .order_by(FinancialRecord.date.desc(), FinancialRecord.created_at.desc())
        .limit(limit)
    ).all()
    return [RecentActivityItem.model_validate(row) for row in rows]


def build_trends(db: Session, months: int = 6) -> list[TrendPoint]:
    period = _period_expression(db)
    income_sum = func.coalesce(
        func.sum(
            case(
                (FinancialRecord.type == RecordType.income, FinancialRecord.amount),
                else_=0,
            )
        ),
        0,
    )
    expense_sum = func.coalesce(
        func.sum(
            case(
                (FinancialRecord.type == RecordType.expense, FinancialRecord.amount),
                else_=0,
            )
        ),
        0,
    )

    rows = db.execute(
        select(
            period.label("period"),
            income_sum.label("income"),
            expense_sum.label("expense"),
        )
        .group_by(period)
        .order_by(period.desc())
        .limit(months)
    ).all()

    ordered_rows = list(reversed(rows))
    return [
        TrendPoint(
            period=row.period,
            income=_decimal(row.income),
            expense=_decimal(row.expense),
            net=(_decimal(row.income) - _decimal(row.expense)).quantize(Decimal("0.01")),
        )
        for row in ordered_rows
    ]
