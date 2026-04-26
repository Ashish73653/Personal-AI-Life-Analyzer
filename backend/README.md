# PALA Backend

FastAPI backend for the Personal AI Life Analyzer (PALA).

This backend covers the Phase 1 core API:

- JWT authentication with access and refresh tokens
- SQLite development database via SQLAlchemy
- Alembic migrations
- CRUD endpoints for usage logs, steps, and expenses
- Standard API response envelope
- Rate limiting
- Query history and insights endpoints prepared for later AI phases

## What is included

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `GET /auth/me`
- `POST /auth/logout`
- `POST /usage`
- `GET /usage`
- `POST /steps`
- `GET /steps`
- `POST /expenses`
- `GET /expenses`
- `PUT /expenses/{id}`
- `DELETE /expenses/{id}`
- `GET /insights`
- `GET /insights/today`
- `POST /query`
- `GET /query/history`
- `GET /health`

## How to run

### 1. Activate the virtual environment

From PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
Set-Location D:\PALA\backend
& D:\PALA\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

If the environment is new or dependencies changed:

```powershell
pip install -r requirements.txt
```

### 3. Apply database migrations

```powershell
alembic upgrade head
```

### 4. Start the API server

```powershell
uvicorn app.main:app --reload
```

Open the API docs at:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc

### 5. Run the smoke test script

```powershell
python test_api.py
```

This script exercises registration, auth, expenses, insights, and query endpoints against the local server.

## Environment variables

The backend reads configuration from `.env`.

Required or commonly used values:

- `DATABASE_URL` - SQLAlchemy connection string, default `sqlite:///./pala.db`
- `SECRET_KEY` - JWT signing secret
- `ACCESS_TOKEN_EXPIRE_MINUTES` - default `15`
- `REFRESH_TOKEN_EXPIRE_DAYS` - default `7`
- `BCRYPT_ROUNDS` - default `12`
- `RATE_LIMIT_PER_MINUTE` - default `60`
- `LLM_MODEL` - default `mistral:7b`
- `EMBEDDING_MODEL` - default `all-MiniLM-L6-v2`
- `LOG_LEVEL` - default `INFO`

Copy `.env.example` to `.env` if you need a fresh local configuration.

## Project layout

### Root files

- `.env` - local environment values for development and testing
- `.env.example` - template of the expected environment variables
- `.gitignore` - ignores virtual environment, local database, and other generated files
- `alembic.ini` - Alembic configuration entry point
- `requirements.txt` - Python dependency list
- `test_api.py` - simple end-to-end smoke test script
- `pala.db` - generated SQLite database file used during local development
- `.venv/` - local Python virtual environment

### `alembic/`

- `alembic/env.py` - Alembic bootstrap that points migrations at the SQLAlchemy models
- `alembic/README` - Alembic template documentation
- `alembic/script.py.mako` - Alembic migration file template
- `alembic/versions/786842c29470_initial_schema.py` - initial schema migration for users, usage logs, steps, expenses, and query history
- `alembic/versions/61f8d9758961_add_query_history.py` - query history table migration
- `alembic/versions/f3a9b7e4c2d1_add_token_version.py` - adds token versioning for JWT revocation and refresh rotation

### `app/`

- `app/__init__.py` - marks the package
- `app/main.py` - FastAPI application entry point, middleware, exception handlers, and router registration
- `app/config.py` - application settings loaded from environment variables
- `app/database.py` - SQLAlchemy engine, session factory, and declarative base
- `app/dependencies.py` - shared FastAPI dependencies for database access and authentication

#### `app/middleware/`

- `app/middleware/__init__.py` - middleware package marker
- `app/middleware/rate_limiter.py` - SlowAPI limiter setup, keyed by authenticated user when possible

#### `app/models/`

- `app/models/__init__.py` - exports all ORM models
- `app/models/user.py` - user account table with UUID id, email, password hash, active flag, and token version
- `app/models/usage_log.py` - daily app usage records
- `app/models/step.py` - daily step count records
- `app/models/expense.py` - expense records with soft delete support
- `app/models/query_history.py` - stored natural-language query history for each user

#### `app/routers/`

- `app/routers/__init__.py` - routers package marker
- `app/routers/auth.py` - register, login, refresh, profile, and logout endpoints
- `app/routers/usage.py` - usage log ingestion and querying endpoints
- `app/routers/steps.py` - step record ingestion and querying endpoints
- `app/routers/expenses.py` - expense CRUD endpoints
- `app/routers/insights.py` - daily and weekly insights endpoints built from analytics service helpers
- `app/routers/query.py` - natural-language query endpoints and query history

#### `app/schemas/`

- `app/schemas/__init__.py` - schemas package marker
- `app/schemas/common.py` - standard API response envelope helpers
- `app/schemas/auth.py` - register, login, token, refresh, and public user schemas
- `app/schemas/usage_log.py` - usage log request and response schemas
- `app/schemas/step.py` - step request and response schemas
- `app/schemas/expense.py` - expense request and response schemas

#### `app/services/`

- `app/services/__init__.py` - services package marker
- `app/services/auth_service.py` - bcrypt password hashing and JWT token creation/decoding
- `app/services/analytics_service.py` - daily and weekly summary builders used by insights and query endpoints

### `tests/`

- `tests/__init__.py` - test package marker

## API behavior notes

- All successful and error responses use the same envelope shape:

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

- Validation, auth, and rate-limit errors are also returned in the same envelope.
- Access tokens and refresh tokens are both versioned so logout and refresh rotation invalidate older tokens.
- SQLite is used for local development, but the SQLAlchemy configuration is PostgreSQL-ready.

## Testing the backend manually

1. Start the server with `uvicorn app.main:app --reload`.
2. Open `http://127.0.0.1:8000/docs`.
3. Call `POST /auth/register` to create a user.
4. Copy the returned access token into the Authorize dialog.
5. Try `POST /expenses`, `GET /usage`, `GET /steps`, and `GET /insights/today`.
6. Run `python test_api.py` for a quick scripted smoke test.

## Notes for future phases

- `app/routers/query.py` and `app/routers/insights.py` are already wired into the API so the Phase 2/3 AI pipeline can be added without changing the client contract.
- `app/services/analytics_service.py` currently provides the daily and weekly summary logic used by those endpoints.

## Quick start summary

```powershell
Set-Location D:\PALA\backend
& D:\PALA\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Then open the docs at `http://127.0.0.1:8000/docs`.
