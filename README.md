# Enterprise Banking Management System

FastAPI backend starter for an enterprise banking project. It uses MySQL, SQLAlchemy ORM, Pydantic schemas, JWT authentication, bcrypt password hashing, and Alembic migrations.

## What is included

- Authentication: registration, login, JWT access token, refresh token, OTP, forgot/reset password, MFA, sessions, role checks, account lockout.
- Customer management: CRUD, KYC verification, addresses, nominees, document metadata, file upload, search.
- Account management: savings, current, fixed deposit, recurring deposit, joint holder, status, JSON/CSV/mock PDF statements.
- Transactions: deposit, withdrawal, fund transfer, UPI, NEFT/RTGS mock, scheduled transfers, beneficiaries, history.
- Loans, cards, branches, employees, notifications, reports, audit/login history, IP tracking, rate limiting.
- Docker, Alembic, unit test, CI workflow, and `/api/v1` API versioning.

## Run locally

```powershell
copy .env.example .env
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
docker compose up -d mysql
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe main.py
```

Open:

- API docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

The first registered user becomes `admin`. Later public registrations become `customer`.

## Run with Docker

```powershell
docker compose up --build
```

This starts MySQL, waits for it to become healthy, runs Alembic migrations, and then starts the FastAPI app.
The Docker MySQL service is available from your host at `127.0.0.1:3307` to avoid conflicts with a local MySQL server on `3306`.

Open:

- API docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

To stop the containers:

```powershell
docker compose down
```

To delete the MySQL data volume and start with a fresh database:

```powershell
docker compose down -v
```

## Official references used

- FastAPI OAuth2/JWT security docs: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- SQLAlchemy ORM quick start: https://docs.sqlalchemy.org/en/20/orm/quickstart.html
- Pydantic models and ORM attribute parsing: https://pydantic.dev/docs/validation/latest/concepts/models/
- Alembic tutorial and autogenerate docs: https://alembic.sqlalchemy.org/en/latest/tutorial.html
