# Phase 2: PALA Android App

Build the Android client that consumes the live FastAPI backend. The goal of this phase is to deliver a working mobile app with authentication, local storage, offline sync, and the first round of behavioral data capture.

## Why this phase comes next

Phase 1 already provides the backend foundation:

- JWT auth endpoints are available
- CRUD endpoints for usage, steps, and expenses are working
- Alembic migrations and SQLite development support are in place
- Postman verification flow is documented

That means Phase 2 can start immediately on top of the live API. Backend work should only resume if mobile integration exposes a contract mismatch or a bug.

## Scope

Phase 2 focuses on the Android app only:

- Register and login screens
- Secure JWT token storage
- Expense entry flow
- Step tracking flow
- App usage tracking flow
- Offline SQLite storage
- Background sync to the backend
- Basic settings and sync status UI

## SRS Requirements Covered

| Req. IDs | Description                                                                     |
| -------- | ------------------------------------------------------------------------------- |
| FR-M1    | Register a new account with email and password strength validation              |
| FR-M2    | Login with JWT access token and refresh token support                           |
| FR-M3    | Logout and clear local credentials                                              |
| FR-M5    | Track usage duration per installed app using UsageStatsManager                  |
| FR-M6    | Record app package name, app label, daily total time spent, and timestamp       |
| FR-M7    | Aggregate usage at day boundaries and persist locally                           |
| FR-M8    | Sync usage data at least once every 24 hours or on reconnection                 |
| FR-M9    | Track daily step count using sensor or Google Fit                               |
| FR-M10   | Record user_id, date, and step count; reset at midnight                         |
| FR-M11   | Run step tracking as a foreground service                                       |
| FR-M12   | Add expense entries with amount, currency, category, description, and timestamp |
| FR-M13   | Edit existing expense entries                                                   |
| FR-M14   | Delete expense entries with soft-delete behavior                                |
| FR-M15   | Support predefined expense categories                                           |
| FR-M16   | Show monthly total and category breakdown                                       |
| FR-M17   | Store collected data in local SQLite with migration support                     |
| FR-M18   | Use idempotent upsert strategy during sync                                      |
| FR-M19   | Use WorkManager with exponential backoff retry                                  |
| FR-M20   | Show sync status in settings                                                    |
| SEC-4    | Encrypt on-device sensitive data                                                |

## Proposed Android Structure

```
android/
├── app/
│   ├── src/main/java/com/pala/
│   │   ├── data/
│   │   │   ├── local/
│   │   │   ├── remote/
│   │   │   └── repository/
│   │   ├── domain/
│   │   ├── ui/
│   │   │   ├── auth/
│   │   │   ├── expenses/
│   │   │   ├── steps/
│   │   │   ├── usage/
│   │   │   └── settings/
│   │   ├── workers/
│   │   └── service/
│   ├── src/main/res/
│   └── build.gradle.kts
├── gradle/
├── settings.gradle.kts
└── README.md
```

## Implementation Plan

### 1. Project setup

- Create the Android project in Kotlin.
- Add core dependencies for Retrofit, Room, WorkManager, DataStore, Coroutines, Hilt, and Compose or XML UI.
- Configure build variants for local API and future production API.

### 2. Authentication flow

- Build register and login screens.
- Store access and refresh tokens securely.
- Add logout support that clears cached tokens and local session state.
- Add token refresh handling when the access token expires.

### 3. Expense flow

- Build the expense form first because it is the simplest end-to-end client flow.
- Add list, edit, and delete screens.
- Sync new and updated expenses to the backend.
- Show monthly totals and category breakdown in the UI.

### 4. Step tracking flow

- Add the step data model and local persistence.
- Implement sensor-based tracking or Google Fit integration.
- Add foreground service support.
- Sync daily step counts to the backend.

### 5. Usage tracking flow

- Request UsageStatsManager permission.
- Aggregate app usage into daily records.
- Store records locally before sync.
- Batch upload usage records to the backend.

### 6. Offline storage and sync

- Use Room as the local SQLite layer.
- Add migrations for schema changes.
- Implement WorkManager jobs for periodic sync and retry handling.
- Make sync idempotent so retrying does not create duplicates.

### 7. Settings and status

- Add sync status, pending records, and last sync time.
- Add account actions such as logout.
- Add toggles for step source and tracking preferences where needed.

## Verification Plan

### Manual checks

- Register a user and confirm the backend returns tokens.
- Log in and confirm the tokens are stored and reused.
- Create, edit, and delete an expense.
- Confirm deleted expenses are hidden from the list.
- Create step and usage records and verify they sync to the backend.
- Put the app offline and confirm records stay queued locally.
- Reconnect and confirm queued records sync successfully.

### API contract checks

- Use Postman to verify the app can talk to the live backend endpoints.
- Confirm token refresh works after expiry.
- Confirm the app handles 401, 422, and 429 responses correctly.

## Definition of Done

Phase 2 is complete when:

- The Android app can register and log in against the live backend.
- Expenses can be created, updated, deleted, and synced.
- Step and usage data can be stored locally and uploaded.
- Offline queueing and sync retry work reliably.
- The app can be tested end to end with the backend already in place.
