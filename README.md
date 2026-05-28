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

## Core Modules

The monolith backend consists of the following decoupled domain modules:
- **Auth & Businesses**: Multi-tenant workspace onboarding, RBAC, and secure JWT verification.
- **Customers, Orders & Payments**: Customer management, transactional order lifecycle, and Paystack payment verification.
- **AI Engine (`app/modules/ai`)**: Sessionless AI operations chat assistant, Markdown performance summaries, and predictive recommendations. Falls back dynamically to local context-aware mock generators if `OPENAI_API_KEY` is not present.
- **Notifications (`app/modules/notifications`)**: Workspace-wide and targeted user notifications dynamically triggered via decoupled system-wide events.
- **Analytics (`app/modules/analytics`)**: High-performance aggregate queries providing overview metrics, revenue history, and order breakdown.
- **WebSocket Gateway (`app/websocket`)**: Bidirectional real-time communication fabric bridging local system events to active user sockets. Supports workspace presence tracking, current resource-view auditing, and streaming AI assistant replies, fanned out horizontally using Redis Pub/Sub.
- **Workflow Automation Engine (`app/modules/workflows`)**: An ultra-scalable, high-throughput rules evaluation system executing custom workflow logic (triggers, multi-operator conditions matching, dynamic template interpolation, and concurrent action execution). Engineered with composite-indexed tables and write-through Redis caches (`opspilot:cache:workflows:*`) to eliminate database query spikes.

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
   docker compose up -d
   ```

5. **Run Migrations**:
   ```bash
   poetry run alembic upgrade head
   ```

6. **Start the Development Server**:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

## Running Tests

We maintain strict verification standards. Ensure the test database exists before executing pytest:
```bash
# Create the test catalog in PostgreSQL container
docker exec opspilot-postgres psql -U opspilot -d opspilot_db -c "CREATE DATABASE opspilot_test_db;"

# Run the complete test suite (All modules passing)
poetry run pytest

# Run specific integration / module suites
poetry run pytest tests/test_workflows.py
poetry run pytest tests/test_websocket.py
poetry run pytest tests/test_phase3.py
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
- **Multi-Tenant Scoping**: All aggregate queries and data modifications strictly filter results using verified JWT workspace boundaries to eliminate IDOR vulnerabilities.
