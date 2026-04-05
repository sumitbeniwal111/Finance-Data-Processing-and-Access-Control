import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _load_project_env_file() -> None:
    if os.getenv("SKIP_PROJECT_ENV_FILE", "").lower() == "true":
        return

    for filename in (".env", ".env.example"):
        path = Path.cwd() / filename
        if not path.exists():
            continue

        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip().strip("\"'")
        break


_load_project_env_file()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Finance Data Processing API")
    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./finance_dashboard.db",
    )
    bootstrap_admin_name: str = os.getenv("BOOTSTRAP_ADMIN_NAME", "System Admin")
    bootstrap_admin_email: str = os.getenv(
        "BOOTSTRAP_ADMIN_EMAIL",
        "admin@example.com",
    )
    bootstrap_admin_token: str = os.getenv(
        "BOOTSTRAP_ADMIN_TOKEN",
        "admin-demo-token",
    )
    auto_seed_demo_data: bool = os.getenv("AUTO_SEED_DEMO_DATA", "false").lower() == "true"


@lru_cache
def get_settings() -> Settings:
    return Settings()
