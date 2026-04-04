# Finance Data Processing and Access Control Backend
FastAPI backend for finance records with role-based access control, dashboard analytics, and PostgreSQL persistence.

## Features
- User management with roles (`viewer`, `analyst`, `admin`) and active/inactive status.
- JWT authentication (`/auth/register`, `/auth/login`, `/auth/me`).
- Admin user management APIs (`/users`).
- Financial records CRUD with filters by type, category, date range, and text search (`/records`).
- Soft delete for records (deleted records are excluded from reads and dashboard analytics).
- In-memory rate limiting for auth and write-heavy endpoints.
- Dashboard summary APIs for totals, category breakdowns, recent activity, and monthly trends (`/dashboard`).
- SQLAlchemy ORM + PostgreSQL via Docker Compose.

## Requirement coverage
- User and role management:
  - User registration and admin-only user CRUD-style management (`create`, `list`, `get`, `update`).
  - Role assignment and active/inactive status are modeled and enforced.
- Financial records management:
  - Record create/read/update/delete APIs with filtering by type, category, date range, and text search.
- Dashboard summary APIs:
  - Total income, total expenses, net balance, category-wise totals, recent activity, monthly trends.
- Access control:
  - Role-based route protection with dependency-based authorization checks.
- Validation and error handling:
  - Pydantic schema validation on inputs.
  - Proper 4xx responses for invalid auth, missing resources, duplicate users, invalid date ranges, and invalid update payloads.
  - `429 Too Many Requests` responses for rate-limited traffic.
- Data persistence:
  - PostgreSQL with SQLAlchemy ORM.

## Role access rules
- `viewer`: dashboard read access only.
- `analyst`: dashboard read access + records read access.
- `admin`: full access (users + records create/update/delete + all reads).

## Quick start
1. Create and run services:
   - `docker compose up --build`
2. API base URL:
   - `http://localhost:8000`
3. Interactive docs:
   - `http://localhost:8000/docs`

## Running tests
- Install dependencies:
  - `pip install -r requirements.txt`
- Run:
  - `pytest -q`

## Authentication flow
1. Register first user:
   - `POST /auth/register`
   - First registered user is auto-assigned `admin`.
2. Login:
   - `POST /auth/login`
   - Returns `access_token`.
3. Use token:
   - `Authorization: Bearer <token>`

## Key endpoints
- Auth:
  - `POST /auth/register`
  - `POST /auth/login`
  - `GET /auth/me`
- Users (admin):
  - `POST /users`
  - `GET /users`
  - `GET /users/{user_id}`
  - `PATCH /users/{user_id}`
- Records:
  - `POST /records` (admin)
  - `GET /records` (admin, analyst) with filters:
    - `record_type`
    - `category`
    - `search` (matches `category` and `description`)
    - `start_date` (`YYYY-MM-DD`)
    - `end_date` (`YYYY-MM-DD`)
  - `GET /records/{record_id}` (admin, analyst)
  - `PATCH /records/{record_id}` (admin)
  - `DELETE /records/{record_id}` (admin)
- Dashboard:
  - `GET /dashboard/summary`
  - `GET /dashboard/category-totals`
  - `GET /dashboard/recent-activity`
  - `GET /dashboard/monthly-trends`

## Notes
- This project uses `Base.metadata.create_all()` for schema creation in development.
- If schema changes are made after initial startup, reset local DB volume:
  - `docker compose down -v`
  - `docker compose up --build`
- `viewer` users can access dashboard endpoints only.
- `analyst` users can read records + dashboard endpoints.
- `admin` users can manage users and records with full privileges.
- Record delete uses soft delete; deleted records are hidden from list/get endpoints and dashboard aggregates.
- Rate limits:
  - `POST /auth/register`: 5 requests/min per client IP
  - `POST /auth/login`: 5 requests/min per client IP
  - Admin user/record write endpoints: 30-60 requests/min per client IP (based on route group)

## Assumptions and tradeoffs
- Authentication is JWT-based with a shared secret for local/dev usage.
- The first registered user is promoted to `admin` to bootstrap the system.
- This implementation focuses on clear service/route separation and role enforcement over advanced production concerns (migrations, observability, distributed caching).
