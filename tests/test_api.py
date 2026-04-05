import os
from pathlib import Path
import sys
import tempfile
import unittest
import uuid

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

TEST_DB_PATH = Path(tempfile.gettempdir()) / f"finance_api_test_{uuid.uuid4().hex}.db"

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["BOOTSTRAP_ADMIN_TOKEN"] = "admin-demo-token"
os.environ["SKIP_PROJECT_ENV_FILE"] = "true"

from fastapi.testclient import TestClient

from app.core.database import SessionLocal, engine
from app.main import app
from app.services.user_service import seed_demo_users


class FinanceApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with TestClient(app):
            pass
        with SessionLocal() as db:
            seed_demo_users(db)

    @classmethod
    def tearDownClass(cls) -> None:
        engine.dispose()
        try:
            if TEST_DB_PATH.exists():
                TEST_DB_PATH.unlink()
        except PermissionError:
            pass

    def setUp(self) -> None:
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)

    def test_healthcheck(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_frontend_login_page_renders(self) -> None:
        response = self.client.get("/app")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Token Sign In", response.text)

    def test_viewer_can_access_dashboard_but_not_records(self) -> None:
        dashboard_response = self.client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": "Bearer viewer-demo-token"},
        )
        records_response = self.client.get(
            "/api/v1/records",
            headers={"Authorization": "Bearer viewer-demo-token"},
        )
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(records_response.status_code, 403)

    def test_admin_can_create_record_and_analyst_can_read_it(self) -> None:
        create_response = self.client.post(
            "/api/v1/records",
            headers={"Authorization": "Bearer admin-demo-token"},
            json={
                "amount": "1500.00",
                "type": "income",
                "category": "Investments",
                "date": "2026-03-20",
                "notes": "Quarterly returns",
            },
        )
        self.assertEqual(create_response.status_code, 201)

        list_response = self.client.get(
            "/api/v1/records",
            headers={"Authorization": "Bearer analyst-demo-token"},
        )
        self.assertEqual(list_response.status_code, 200)
        self.assertGreaterEqual(list_response.json()["total"], 1)

    def test_invalid_record_payload_returns_validation_error(self) -> None:
        response = self.client.post(
            "/api/v1/records",
            headers={"Authorization": "Bearer admin-demo-token"},
            json={
                "amount": "-10.00",
                "type": "expense",
                "category": "Ops",
                "date": "2026-03-20",
            },
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
