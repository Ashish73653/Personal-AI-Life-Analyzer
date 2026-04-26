# Phase 1: PALA Backend Core

Build the FastAPI backend server with JWT authentication, 4 database tables, Alembic migrations, and RESTful CRUD endpoints — the API foundation that both the Android app and web dashboard will consume.

## SRS Requirements Covered

| Req. IDs | Description |
|----------|-------------|
| FR-B1 | `POST /auth/register` and `POST /auth/login` (public, return JWT access + refresh tokens) |
| FR-B2 | CRUD for usage logs: `POST /usage`, `GET /usage` |
| FR-B3 | CRUD for step records: `POST /steps`, `GET /steps` |
| FR-B4 | CRUD for expenses: `POST /expenses`, `GET /expenses`, `PUT /expenses/{id}`, `DELETE /expenses/{id}` |
| FR-B5 | Consistent response envelope `{"success": bool, "data": ..., "error": ...}` |
| FR-B6 | Appropriate HTTP status codes (200, 201, 400, 401, 403, 404, 422, 500) |
| FR-B7 | Relational DB (SQLite for dev, PostgreSQL-ready for production) |
| FR-B8 | FK constraints, unique indexes on `(user_id, date)`, cascading deletes |
| FR-B9 | Alembic-managed, reversible migrations |
| SEC-2 | JWT access tokens (15 min default), refresh tokens (7 days), rotation on use |
| SEC-3 | bcrypt password hashing (cost factor ≥ 12) |
| SEC-5 | Rate limiting (60 req/min per user) |
| SEC-6 | Parameterized queries (via SQLAlchemy ORM) |
| NFR-B4 | bcrypt cost factor ≥ 12 |
| NFR-B5 | Structured JSON logging |

## Open Questions

> [!IMPORTANT]
> **Database choice for development:** The SRS specifies SQLite for dev and PostgreSQL for production. I'll use **SQLite** for now with SQLAlchemy so it's trivially swappable later. Is this OK, or do you want PostgreSQL from the start?

> [!NOTE]
> **Virtual environment:** I'll create a Python virtual environment at `d:\PALA\backend\.venv` to isolate dependencies. Python 3.13.2 is available on your system.

---

## Proposed Project Structure

```
d:\PALA\backend\
├── .env                          # Environment variables (secrets, config)
├── .env.example                  # Template for env vars (committed to VCS)
├── requirements.txt              # Pinned Python dependencies
├── alembic.ini                   # Alembic configuration
├── alembic/                      # Alembic migrations directory
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_schema.py
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Settings via pydantic-settings
│   ├── database.py               # SQLAlchemy engine, session, Base
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py               # Users table
│   │   ├── usage_log.py          # Usage Logs table
│   │   ├── step.py               # Steps table
│   │   └── expense.py            # Expenses table
│   ├── schemas/                  # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── common.py             # Envelope response model
│   │   ├── auth.py               # Register/Login schemas
│   │   ├── usage_log.py
│   │   ├── step.py
│   │   └── expense.py
│   ├── routers/                  # FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── auth.py               # /auth/register, /auth/login
│   │   ├── usage.py              # /usage
│   │   ├── steps.py              # /steps
│   │   └── expenses.py           # /expenses
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py       # Password hashing, JWT generation
│   │   └── user_service.py       # User CRUD
│   ├── middleware/                # Custom middleware
│   │   ├── __init__.py
│   │   └── rate_limiter.py       # Per-user rate limiting
│   └── dependencies.py           # Shared FastAPI dependencies (get_db, get_current_user)
└── tests/                        # (placeholder for future tests)
    └── __init__.py
```

---

## Proposed Changes

### 1. Environment & Dependencies

#### [NEW] [requirements.txt](file:///d:/PALA/backend/requirements.txt)
```
fastapi[standard]>=0.115.0
uvicorn[standard]>=0.30.0
sqlalchemy>=2.0.0
alembic>=1.13.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.9
slowapi>=0.1.9
python-dotenv>=1.0.0
```

#### [NEW] [.env.example](file:///d:/PALA/backend/.env.example)
- `DATABASE_URL` — SQLite connection string (default: `sqlite:///./pala.db`)
- `SECRET_KEY` — JWT signing key (auto-generated on first run)
- `ACCESS_TOKEN_EXPIRE_MINUTES` — Default 15
- `REFRESH_TOKEN_EXPIRE_DAYS` — Default 7
- `BCRYPT_ROUNDS` — Default 12
- `LLM_MODEL` — For future AI phase (`mistral:7b`)

---

### 2. Configuration

#### [NEW] [config.py](file:///d:/PALA/backend/app/config.py)
- Pydantic `Settings` class loading from `.env`
- All SRS-mandated defaults: token expiry, bcrypt rounds, rate limits
- Database URL with SQLite default, PostgreSQL-ready

---

### 3. Database Layer

#### [NEW] [database.py](file:///d:/PALA/backend/app/database.py)
- SQLAlchemy async-compatible engine creation
- `SessionLocal` factory
- `Base` declarative base
- `get_db` dependency for session injection

#### [NEW] Models (4 files in `app/models/`)

| Model | Table | Key Constraints (from SRS §6.2) |
|-------|-------|--------------------------------|
| `User` | `users` | PK: UUID v4, `email` UNIQUE, `password_hash` NOT NULL, `is_active` DEFAULT TRUE |
| `UsageLog` | `usage_logs` | FK → `users.id` CASCADE, `app_package` + `recorded_date` per user |
| `Step` | `steps` | FK → `users.id` CASCADE, UNIQUE on `(user_id, step_date)` |
| `Expense` | `expenses` | FK → `users.id` CASCADE, `NUMERIC(12,2)`, `is_deleted` soft-delete |

---

### 4. Pydantic Schemas

#### [NEW] [common.py](file:///d:/PALA/backend/app/schemas/common.py)
Standard envelope per FR-B5:
```python
class APIResponse(BaseModel):
    success: bool
    data: Any = None
    error: str | None = None
```

#### [NEW] Auth, Usage, Steps, Expense schemas
- Request validation (password strength: min 8 chars, 1 uppercase, 1 digit per FR-M1)
- Response serialization with proper types

---

### 5. Authentication (JWT)

#### [NEW] [auth_service.py](file:///d:/PALA/backend/app/services/auth_service.py)
- `hash_password(plain)` → bcrypt with cost factor ≥ 12
- `verify_password(plain, hashed)` → bool
- `create_access_token(user_id)` → JWT (15 min expiry)
- `create_refresh_token(user_id)` → JWT (7 day expiry)
- `decode_token(token)` → payload dict

#### [NEW] [dependencies.py](file:///d:/PALA/backend/app/dependencies.py)
- `get_current_user` — Extracts and validates JWT from `Authorization: Bearer <token>` header, returns the authenticated user
- `get_db` — Yields a SQLAlchemy session

---

### 6. API Routers

#### [NEW] [auth.py](file:///d:/PALA/backend/app/routers/auth.py) — Public
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | Create user, return tokens |
| `/auth/login` | POST | Validate credentials, return tokens |
| `/auth/refresh` | POST | Rotate refresh token, return new pair |

#### [NEW] [usage.py](file:///d:/PALA/backend/app/routers/usage.py) — Protected
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/usage` | POST | Submit usage log(s) — supports batch upsert |
| `/usage` | GET | Query by `date`, `start`/`end` range |

#### [NEW] [steps.py](file:///d:/PALA/backend/app/routers/steps.py) — Protected
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/steps` | POST | Submit step record — upsert on `(user_id, step_date)` |
| `/steps` | GET | Query by `start`/`end` date range |

#### [NEW] [expenses.py](file:///d:/PALA/backend/app/routers/expenses.py) — Protected
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/expenses` | POST | Create expense |
| `/expenses` | GET | List expenses (filtered, paginated, excludes soft-deleted) |
| `/expenses/{id}` | PUT | Update expense |
| `/expenses/{id}` | DELETE | Soft-delete expense |

---

### 7. Middleware & Cross-Cutting

#### [NEW] [rate_limiter.py](file:///d:/PALA/backend/app/middleware/rate_limiter.py)
- SlowAPI integration: 60 requests/minute per authenticated user (SEC-5)

#### [NEW] [main.py](file:///d:/PALA/backend/app/main.py)
- FastAPI app instance with metadata (title, version, description)
- Include all routers with prefixes
- CORS middleware (permissive for dev, restrictable later)
- Rate limiter middleware
- Structured JSON logging (NFR-B5)
- Startup event: create tables if needed

---

### 8. Alembic Migrations

#### [NEW] [alembic.ini](file:///d:/PALA/backend/alembic.ini) + [alembic/env.py](file:///d:/PALA/backend/alembic/env.py)
- Configured to read `DATABASE_URL` from `.env`
- Targets `app.database.Base.metadata`

#### [NEW] [001_initial_schema.py](file:///d:/PALA/backend/alembic/versions/001_initial_schema.py)
- Creates all 4 tables with full constraints
- Reversible `downgrade()` drops all tables

---

## Verification Plan

### Automated Tests
1. **Server startup**: `py -m uvicorn app.main:app` — verify server boots without errors
2. **API contract tests via browser/Postman**:
   - `POST /auth/register` with valid/invalid payloads
   - `POST /auth/login` with correct/wrong credentials
   - All CRUD endpoints with JWT token
   - Verify response envelope format on every response
3. **Alembic migration**: `alembic upgrade head` + `alembic downgrade base` round-trip
4. **Database inspection**: Verify tables, constraints, and indexes are created correctly

### Manual Verification
- Hit all endpoints via the FastAPI interactive docs at `http://localhost:8000/docs`
- Confirm JWT token lifecycle (issue → use → expire → refresh)
- Confirm rate limiting kicks in after 60 rapid requests
