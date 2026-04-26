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

## Postman verification guide

Use this section to confirm the backend works from Postman step by step.

### 1. Create a Postman environment

Create these variables in a Postman environment:

- `base_url` = `http://127.0.0.1:8000`
- `access_token` = leave empty at first
- `refresh_token` = leave empty at first
- `expense_id` = leave empty at first

Use `{{base_url}}` in all requests.

### 2. Recommended request order

Run the requests in this order so each later scenario has the data it needs:

1. Health check
2. Register user
3. Login user
4. Refresh token
5. Get current user profile
6. Create usage log
7. Read usage logs
8. Create step record
9. Read step records
10. Create expense
11. Read expenses
12. Update expense
13. Delete expense
14. Verify deleted expense is hidden
15. Get insights
16. Get query history
17. Logout and verify revoked token
18. Rate-limit check

### 3. General Postman setup

- Method: use the HTTP method shown for each scenario.
- Headers: add `Content-Type: application/json` for all `POST`, `PUT`, and `DELETE` requests.
- Authorization: use `Bearer Token` with `{{access_token}}` for protected routes.
- Body: use `raw` and `JSON` for request payloads.

### 4. Scenario checklist

#### Scenario 1: Health check

- Request: `GET {{base_url}}/health`
- Expected status: `200`
- Expected body:

```json
{
  "success": true,
  "data": {
    "status": "healthy"
  },
  "error": null
}
```

#### Scenario 2: Register a new user

- Request: `POST {{base_url}}/auth/register`
- Body:

```json
{
  "email": "postman.user@example.com",
  "password": "TestPass123"
}
```

- Expected status: `201`
- Expected checks:
  - `success` is `true`
  - response contains `data.user.id`
  - response contains `data.tokens.access_token`
  - response contains `data.tokens.refresh_token`

Save the returned tokens into Postman environment variables if you want:

- `access_token` = `data.tokens.access_token`
- `refresh_token` = `data.tokens.refresh_token`

#### Scenario 3: Register with duplicate email

- Request: repeat the register request with the same email
- Expected status: `409`
- Expected checks:
  - `success` is `false`
  - `error` says the account already exists

#### Scenario 4: Login with valid credentials

- Request: `POST {{base_url}}/auth/login`
- Body:

```json
{
  "email": "postman.user@example.com",
  "password": "TestPass123"
}
```

- Expected status: `200`
- Expected checks:
  - `success` is `true`
  - response contains fresh `access_token` and `refresh_token`

#### Scenario 5: Login with invalid credentials

- Request: same login endpoint with a wrong password
- Expected status: `401`
- Expected checks:
  - `success` is `false`
  - `error` says invalid email or password

#### Scenario 6: Get current user profile

- Request: `GET {{base_url}}/auth/me`
- Authorization: Bearer `{{access_token}}`
- Expected status: `200`
- Expected checks:
  - `success` is `true`
  - response contains user `id`, `email`, and `created_at`

#### Scenario 7: Refresh token

- Request: `POST {{base_url}}/auth/refresh`
- Body:

```json
{
  "refresh_token": "{{refresh_token}}"
}
```

- Expected status: `200`
- Expected checks:
  - `success` is `true`
  - response contains a new token pair

Important: after refresh, update your stored environment variables with the new tokens because the old refresh token becomes invalid.

#### Scenario 8: Reuse old refresh token after rotation

- Request: call `/auth/refresh` again using the previous refresh token
- Expected status: `401`
- Expected checks:
  - `success` is `false`
  - `error` says the refresh token has been revoked

#### Scenario 9: Create usage log

- Request: `POST {{base_url}}/usage`
- Authorization: Bearer `{{access_token}}`
- Body:

```json
{
  "logs": [
    {
      "app_package": "com.instagram.android",
      "app_label": "Instagram",
      "time_spent_sec": 3600,
      "recorded_date": "2026-04-26"
    }
  ]
}
```

- Expected status: `201`
- Expected checks:
  - `success` is `true`
  - response contains the saved log record

#### Scenario 10: Read usage logs

- Request: `GET {{base_url}}/usage?recorded_date=2026-04-26`
- Authorization: Bearer `{{access_token}}`
- Expected status: `200`
- Expected checks:
  - `success` is `true`
  - response returns the log you inserted

#### Scenario 11: Create step record

- Request: `POST {{base_url}}/steps`
- Authorization: Bearer `{{access_token}}`
- Body:

```json
{
  "step_count": 8500,
  "step_date": "2026-04-26",
  "source": "sensor"
}
```

- Expected status: `201`
- Expected checks:
  - `success` is `true`
  - response contains the saved step record

#### Scenario 12: Read step records

- Request: `GET {{base_url}}/steps?start=2026-04-01&end=2026-04-30`
- Authorization: Bearer `{{access_token}}`
- Expected status: `200`
- Expected checks:
  - `success` is `true`
  - response contains the step record you inserted

#### Scenario 13: Create expense

- Request: `POST {{base_url}}/expenses`
- Authorization: Bearer `{{access_token}}`
- Body:

```json
{
  "amount": 250.5,
  "currency": "INR",
  "category": "Food & Dining",
  "description": "Lunch",
  "expense_at": "2026-04-26T12:00:00Z"
}
```

- Expected status: `201`
- Expected checks:
  - `success` is `true`
  - response contains `data.id`

Save the returned `data.id` into `expense_id`.

#### Scenario 14: Read expenses

- Request: `GET {{base_url}}/expenses`
- Authorization: Bearer `{{access_token}}`
- Expected status: `200`
- Expected checks:
  - `success` is `true`
  - response contains your expense in `data.items`

#### Scenario 15: Update expense

- Request: `PUT {{base_url}}/expenses/{{expense_id}}`
- Authorization: Bearer `{{access_token}}`
- Body:

```json
{
  "amount": 300.0,
  "description": "Lunch with tea"
}
```

- Expected status: `200`
- Expected checks:
  - `success` is `true`
  - updated fields are reflected in the response

#### Scenario 16: Delete expense

- Request: `DELETE {{base_url}}/expenses/{{expense_id}}`
- Authorization: Bearer `{{access_token}}`
- Expected status: `200`
- Expected checks:
  - `success` is `true`
  - response confirms the expense was deleted

#### Scenario 17: Confirm soft delete

- Request: `GET {{base_url}}/expenses`
- Authorization: Bearer `{{access_token}}`
- Expected status: `200`
- Expected checks:
  - the deleted expense no longer appears in `data.items`

#### Scenario 18: Get insights

- Request: `GET {{base_url}}/insights?type=daily&date=2026-04-26`
- Authorization: Bearer `{{access_token}}`
- Expected status: `200`
- Expected checks:
  - `success` is `true`
  - response contains daily summary fields such as `narrative`, `screen_time_hours`, and `step_count`

You can also test weekly insights:

- Request: `GET {{base_url}}/insights?type=weekly&date=2026-04-26`

#### Scenario 19: Get query history

- Request: `GET {{base_url}}/query/history`
- Authorization: Bearer `{{access_token}}`
- Expected status: `200`
- Expected checks:
  - `success` is `true`
  - response is an array of saved query history items

#### Scenario 20: Logout and verify token revocation

- Request: `POST {{base_url}}/auth/logout`
- Authorization: Bearer `{{access_token}}`
- Expected status: `200`
- Expected checks:
  - `success` is `true`

Then call `GET {{base_url}}/auth/me` again with the same access token.

- Expected status: `401`
- Expected checks:
  - `success` is `false`
  - `error` says the token has been revoked

#### Scenario 21: Rate limit check

- Request: send the same authenticated request repeatedly, for example `GET {{base_url}}/auth/me`
- Expected status after enough requests: `429`
- Expected checks:
  - `success` is `false`
  - `error` says rate limit exceeded

### 5. What to verify in every response

For every request, confirm these points:

- `success` is present
- `data` is present
- `error` is present
- success responses have `error: null`
- error responses have `success: false`

### 6. Common failure checks

- If `/auth/me` returns `401`, confirm the token is present in the Authorization header and starts with `Bearer `.
- If `/expenses` or `/steps` returns `401`, confirm you are using the latest access token after refresh.
- If `/auth/refresh` returns `401`, the refresh token was already rotated or is invalid.
- If `POST /expenses` returns `422`, check the JSON body format and date/time string format.
- If `429` appears too early, lower the request rate or wait for the limit window to reset.

### 7. Quick success path

If you want the fastest full check in Postman, run just these requests first:

1. `GET /health`
2. `POST /auth/register`
3. `GET /auth/me`
4. `POST /expenses`
5. `GET /expenses`
6. `POST /auth/logout`
7. `GET /auth/me` again with the same token

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
