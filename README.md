# Finance Data Processing and Access Control Backend

A backend assignment submission built with Python, FastAPI, SQLAlchemy, and MySQL-compatible persistence. The API focuses on clean structure, role-based access control, financial record management, and dashboard-friendly aggregation endpoints.

## Tech Stack

- Python 3.11
- FastAPI
- SQLAlchemy ORM
- MySQL via `PyMySQL`
- SQLite fallback for quick local runs and tests

## Why FastAPI + SQLAlchemy + MySQL

- FastAPI keeps the API layer concise and strongly validated.
- SQLAlchemy gives a clean service/model split and works well with both MySQL and SQLite.
- MySQL matches your preferred stack and is suitable for structured financial data.
- SQLite is included only as a low-friction local fallback so the project can be reviewed quickly without extra infrastructure.

## Features

- User management with roles: `viewer`, `analyst`, `admin`
- User status support: `active`, `inactive`
- Token-based mock authentication for local/demo use
- Role-based access control enforced at the backend dependency layer
- Financial record CRUD
- Filtering and pagination for record listing
- Dashboard summary APIs for totals, trends, category totals, and recent activity
- Input validation and consistent JSON error responses
- Bootstrap admin creation on first startup
- Demo data seeding for quick evaluation
- Lightweight Jinja2 frontend for quick manual review at `/app`

## Access Control Matrix

| Capability | Viewer | Analyst | Admin |
| --- | --- | --- | --- |
| View dashboard summary | Yes | Yes | Yes |
| View category totals | Yes | Yes | Yes |
| View trends / recent activity | Yes | Yes | Yes |
| View financial records | No | Yes | Yes |
| Create / update / delete financial records | No | No | Yes |
| Create / update users | No | No | Yes |
| Rotate user tokens | No | No | Yes |

## Project Structure

```text
app/
  api/
    dependencies.py
    routes/
  core/
  models/
  schemas/
  services/
  main.py
  seed.py
tests/
requirements.txt
docker-compose.yml
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

The app now reads project env files automatically.

Recommended approach:

1. Copy `.env.example` to `.env`
2. Put your local database URI in `.env`

Fallback:

- if `.env` is missing, the app will read `.env.example`

Important variables:

- `DATABASE_URL`
- `BOOTSTRAP_ADMIN_EMAIL`
- `BOOTSTRAP_ADMIN_TOKEN`
- `AUTO_SEED_DEMO_DATA`

Example MySQL connection:

```env
DATABASE_URL=mysql+pymysql://finance_user:finance_password@127.0.0.1:3306/finance_dashboard
```

### 3. Start MySQL

If you want a local MySQL instance quickly:

```bash
docker compose up -d
```

### 4. Run the API

```bash
uvicorn app.main:app --reload
```

You can then open:

- Swagger docs: `http://127.0.0.1:8000/docs`
- Simple frontend: `http://127.0.0.1:8000/app`

The app will automatically:

- create tables on startup
- create a bootstrap admin if no admin exists

Default bootstrap admin token:

```text
admin-demo-token
```

Default bootstrap admin email:

```text
admin@example.com
```

### 5. Seed demo records

```bash
python -m app.seed
```

This seeds:

- analyst demo user: `analyst@example.com` / `analyst-demo-token`
- viewer demo user: `viewer@example.com` / `viewer-demo-token`
- sample financial records for dashboard testing

## Authentication

This project uses a simple token-based mock authentication flow to keep the assignment focused on backend logic rather than production auth.

Pass the token in the header:

```http
Authorization: Bearer admin-demo-token
```

Tokens are stored as SHA-256 hashes in the database.

## Simple Frontend

The frontend is intentionally small and server-rendered with Jinja2 so the project still reads as a backend-first assignment.

- `GET /app` for token sign-in
- `GET /app/dashboard` for summary analytics
- `GET /app/records` for record inspection and filtering
- `GET /app/users` for admin-only user management

Use one of the seeded demo tokens to sign in:

- `admin-demo-token`
- `analyst-demo-token`
- `viewer-demo-token`

## Core API Endpoints

### Health

- `GET /`

### Auth

- `GET /api/v1/auth/me`

### Users

- `POST /api/v1/users`
- `GET /api/v1/users`
- `GET /api/v1/users/{user_id}`
- `PATCH /api/v1/users/{user_id}`
- `POST /api/v1/users/{user_id}/rotate-token`
- `POST /api/v1/users/seed/demo`

### Records

- `POST /api/v1/records`
- `GET /api/v1/records`
- `GET /api/v1/records/{record_id}`
- `PATCH /api/v1/records/{record_id}`
- `DELETE /api/v1/records/{record_id}`

Supported filters on `GET /api/v1/records`:

- `type`
- `category`
- `start_date`
- `end_date`
- `min_amount`
- `max_amount`
- `page`
- `page_size`

### Dashboard

- `GET /api/v1/dashboard/summary`
- `GET /api/v1/dashboard/category-totals`
- `GET /api/v1/dashboard/recent-activity`
- `GET /api/v1/dashboard/trends`

## Example Requests

### Create a record as admin

```bash
curl -X POST http://127.0.0.1:8000/api/v1/records \
  -H "Authorization: Bearer admin-demo-token" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "1500.00",
    "type": "income",
    "category": "Investments",
    "date": "2026-03-20",
    "notes": "Quarterly returns"
  }'
```

### View dashboard summary as viewer

```bash
curl http://127.0.0.1:8000/api/v1/dashboard/summary \
  -H "Authorization: Bearer viewer-demo-token"
```

## Assumptions and Tradeoffs

- Authentication is intentionally simplified to static bearer tokens so the focus stays on access control and business logic.
- Records are global to the finance dashboard rather than scoped per individual user.
- Database tables are created automatically on startup instead of using migrations to keep the assignment lightweight.
- SQLite is supported for reviewer convenience, but MySQL is the intended primary database.

## Validation and Error Handling

- Pydantic validates request bodies and query params.
- Invalid roles, malformed input, and missing required fields return `422`.
- Unauthorized or forbidden actions return `401` or `403`.
- Missing resources return `404`.
- Business-rule violations such as duplicate email return `400`.

## Testing

The repository includes a lightweight unittest-based API smoke suite:

```bash
python tests/test_api.py
```

The tests cover:

- health endpoint
- frontend login page render
- viewer restrictions
- admin create + analyst read flow
- validation failure on invalid record input

## Possible Next Improvements

- Replace mock tokens with JWT authentication
- Add Alembic migrations
- Add audit logs for record and user changes
- Add soft delete and restore flows
- Expand automated tests around summaries and filters
