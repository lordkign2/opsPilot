# OpsPilot Backend

OpsPilot is an AI-powered business operations platform tailored for SMEs. This repository contains the FastAPI backend, built with strict enterprise engineering standards, clean architecture, and horizontal scalability in mind.

## Architecture

We follow a strict **Layered Architecture** enforced across the codebase:
- **Routers** (`routes.py`): HTTP concerns, request validation, response formatting.
- **Services** (`service.py`): Core business logic, orchestration, and domain rules.
- **Repositories** (`repository.py`): Database abstractions using SQLAlchemy.

For detailed engineering standards, refer to [RULES.md](RULES.md).

## Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (via `asyncpg` and `SQLAlchemy`)
- **Caching & Pub/Sub**: Redis
- **Authentication**: OAuth2 with JWT
- **Package Management**: Poetry
- **Static Analysis**: Ruff, MyPy, Black, pre-commit

## Getting Started

### Prerequisites
- Python 3.10+
- Poetry
- Docker & Docker Compose (for DB and Redis)

### Installation

1. **Install dependencies**:
   ```bash
   poetry install
   ```

2. **Set up pre-commit hooks**:
   ```bash
   poetry run pre-commit install
   ```

3. **Configure Environment**:
   Copy `.env.example` to `.env` and fill in your secrets.
   ```bash
   cp .env.example .env
   ```

4. **Start Infrastructure**:
   ```bash
   docker-compose up -d
   ```

5. **Run Migrations**:
   ```bash
   poetry run alembic upgrade head
   ```

6. **Start the Development Server**:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

## Production Deployment
The application is designed to be run behind a reverse proxy/API Gateway (e.g., Kong) and served via Gunicorn with Uvicorn workers for optimal async performance:
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Security & Compliance
- **SOC2 Audit Trails**: Critical actions are immutably logged via the internal `audit` module.
- **Secret Management**: Sensitive variables are strictly typed as `SecretStr` to prevent memory leaks.
- **Token Blacklisting**: JWTs are invalidated via Redis upon logout or password change.
