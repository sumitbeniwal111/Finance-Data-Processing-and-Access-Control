from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.models.enums import RecordType
from app.models.financial_record import FinancialRecord
from app.models.user import User
from app.services.user_service import ensure_bootstrap_admin, seed_demo_users

settings = get_settings()


def seed_records() -> int:
    with SessionLocal() as db:
        init_db()
        bootstrap_result = ensure_bootstrap_admin(db)
        admin = bootstrap_result[0] if bootstrap_result else db.scalar(
            select(User).where(User.email == settings.bootstrap_admin_email.lower())
        )
        if admin is None:
            raise RuntimeError("Unable to create or locate an admin user for seeding.")

        existing_count = db.scalar(select(FinancialRecord.id).limit(1))
        if existing_count is not None:
            return 0

        seed_demo_users(db)
        records = [
            FinancialRecord(
                amount=Decimal("8500.00"),
                type=RecordType.income,
                category="Salary",
                date=date(2026, 1, 5),
                notes="January salary",
                created_by_user_id=admin.id,
            ),
            FinancialRecord(
                amount=Decimal("2100.00"),
                type=RecordType.expense,
                category="Operations",
                date=date(2026, 1, 12),
                notes="Software and tooling",
                created_by_user_id=admin.id,
            ),
            FinancialRecord(
                amount=Decimal("1800.00"),
                type=RecordType.expense,
                category="Marketing",
                date=date(2026, 2, 3),
                notes="Campaign spend",
                created_by_user_id=admin.id,
            ),
            FinancialRecord(
                amount=Decimal("9200.00"),
                type=RecordType.income,
                category="Consulting",
                date=date(2026, 2, 28),
                notes="Client billing",
                created_by_user_id=admin.id,
            ),
            FinancialRecord(
                amount=Decimal("1350.00"),
                type=RecordType.expense,
                category="Travel",
                date=date(2026, 3, 15),
                notes="Investor meetings",
                created_by_user_id=admin.id,
            ),
        ]
        db.add_all(records)
        db.commit()
        return len(records)


if __name__ == "__main__":
    seeded_count = seed_records()
    print(f"Seeded {seeded_count} financial records.")
