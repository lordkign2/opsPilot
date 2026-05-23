# OpsPilot Architectural Rules & Engineering Standards

**Author:** Principal Software Engineer & Architecture Review Lead  
**Scope:** `opspilot-backend` (FastAPI / Async SQLAlchemy)  
**Status:** ENFORCED  

This document outlines the architectural patterns, engineering standards, and security requirements for the OpsPilot backend. It is the definitive guide for how code is written in this repository. Rules are non-negotiable unless explicitly waived by an Architecture Review.

---

## 1. Core Architecture & Layering

### 1.1 Strict Layering / Clean Architecture
**[REQUIRED]** The application enforces a strict three-tier architecture: Router → Service → Repository. 
- **API Layer (Routers)** handle HTTP concerns (request parsing, validation, response formatting).
- **Service Layer** contains core business logic, orchestration, rules, and event emission.
- **Repository Layer** abstracts database interactions (e.g., SQLAlchemy queries).

**[PROHIBITED]** Do not inject database sessions (`AsyncSession`) directly into routers. Do not write business logic or execute queries in the routing layer.

### 1.2 Centralised Registration
**[OBSERVED]** The application uses `app.core.registry.py` to mount all module routers and event handlers.
**[REQUIRED]** Do not modify `main.py` when adding a new module. All new module routers MUST be registered in `app.core.registry`.

### 1.3 Dependency Injection (DI)
**[REQUIRED]** Use FastAPI's built-in DI system (`Depends`) to manage database sessions, authentication context, and external clients. Do not instantiate singletons globally where request scope is required.

---

## 2. Database & Data Access

### 2.1 Base Repository Pattern
**[OBSERVED]** A generic `BaseRepository` exists in `app.shared.base_repository`.
**[REQUIRED]** All domain repositories MUST inherit from `BaseRepository`. 
**[PROHIBITED]** Do not duplicate standard CRUD methods (`get_by_id`, `create`, `update`, `delete`, `get_many`) in domain repositories.

### 2.2 Multi-Tenancy (Business Scoping)
**[OBSERVED]** The system is multi-tenant, partitioned by `business_id`.
**[REQUIRED]** Every query fetching business-owned data MUST explicitly filter by `business_id` using the scoped methods in `BaseRepository` (e.g., `get_by_business`).
**[DANGEROUS]** Querying resources globally (without a business context filter) is a critical data exposure risk and is strictly forbidden outside of super-admin contexts.

### 2.3 Synchronous Operations
**[PROHIBITED]** The database engine is `asyncpg`. Synchronous SQLAlchemy operations or blocking calls within the event loop are strictly prohibited.

---

## 3. Security & Compliance

### 3.1 Authentication & Authorization
**[OBSERVED]** OAuth2 with JWT tokens is implemented.
**[REQUIRED]** All secure endpoints must enforce JWT access. Implement Role-Based Access Control (RBAC) via middleware or dependencies for complex permission structures.

### 3.2 Token Invalidation
**[OBSERVED]** Redis is used to blacklist JWTs upon logout.
**[REQUIRED]** Every state-changing authentication event (logout, password change) MUST blacklist the current tokens in Redis. 

### 3.3 Secret & Environment Management
**[REQUIRED]** All sensitive configurations (e.g., `JWT_SECRET_KEY`, `DATABASE_URL`) MUST be typed as Pydantic's `SecretStr` to prevent accidental logging or exposure in memory dumps.
**[REQUIRED]** Use environment-level encryption and secrets management solutions (e.g., AWS Secrets Manager, HashiCorp Vault) in production instead of plain `.env` files.

### 3.4 Enterprise Compliance (SOC2 / GDPR)
**[REQUIRED]** The system must maintain detailed audit trails with user attribution and timestamping for all critical mutation operations. All audit events must be logged securely and immutably to comply with SOC2 and GDPR.

### 3.5 Password Hashing
**[REQUIRED]** All password hashes MUST use the centralised `hash_password` and `verify_password` utilities in `app.core.security`. Custom crypto implementations are forbidden.

---

## 4. Production Deployment & Scalability

### 4.1 Server Stack
**[REQUIRED]** Run applications using Gunicorn with Uvicorn workers (`uvicorn.workers.UvicornWorker`) to ensure horizontal scaling across CPU cores in production.

### 4.2 Asynchronous I/O Discipline
**[REQUIRED]** Use `async/await` strictly for I/O-bound tasks (database, external APIs, Redis).
**[DANGEROUS]** Avoid using `async` for purely CPU-bound tasks (e.g., heavy crypto, image processing). Offload CPU-bound work to background workers (like Celery) or thread pools to prevent blocking the async event loop.

### 4.3 API Gateway
**[RECOMMENDED]** For large-scale enterprise deployments, position an API Gateway (e.g., Kong, Zuplo) in front of the FastAPI application to manage rate-limiting, edge security, WAF, and cross-service observability.

---

## 5. Error Handling & Responses

### 5.1 Response Envelopes
**[OBSERVED]** A unified response format exists in `app.shared.response.py`.
**[REQUIRED]** All successful API responses MUST be wrapped using `success_response` or `paginated_response`. 
**[PROHIBITED]** Do not return raw Pydantic models, dicts, or lists directly from route handlers.

### 5.2 Exception Management
**[OBSERVED]** A custom exception hierarchy descends from `OpsPilotException` in `app.core.exceptions`.
**[REQUIRED]** Raise specific domain exceptions (e.g., `NotFoundError`, `UnauthorizedError`). The global exception handler will automatically translate these into standard JSON error envelopes.
**[DANGEROUS]** Do not catch generic `Exception` objects in business logic without re-raising, as it masks underlying system failures and prevents the global error handler from logging them correctly.
**[PROHIBITED]** Never return `JSONResponse` manually with 4xx/5xx status codes from a router or service. Always raise an exception.

---

## 6. Observability & Auditing

### 6.1 Logging Discipline
**[REQUIRED]** Use the application logger (`get_logger(__name__)`).
**[PROHIBITED]** The use of `print()` statements for debugging or output is banned in production code.

### 6.2 Event-Driven Side Effects
**[OBSERVED]** An asynchronous event bus exists (`app.core.events`).
**[REQUIRED]** Use the event bus for all non-critical side effects (e.g., sending welcome emails, triggering analytics). Do not block the primary HTTP request lifecycle for these tasks.

---

## 7. Code Quality & Tooling

### 7.1 Type Safety
**[REQUIRED]** Strictly enforce Python type hints across the entire codebase. Use Pydantic models for all data validation and serialization.

### 7.2 Static Analysis
**[REQUIRED]** The codebase must integrate static analysis tools. Use Ruff for linting, MyPy for static typing, and Pre-commit hooks to maintain a clean and consistent repository.

### 7.3 Testing Strategy
**[REQUIRED]** Maintain high reliability with a comprehensive testing strategy. Write unit tests with Pytest and ensure critical paths are covered by end-to-end (e2e) tests.

### 7.4 Package Management
**[REQUIRED]** Use modern tools like **Poetry** for predictable and deterministic dependency management. Standard `requirements.txt` or `setuptools` are legacy and deprecated for this project.

---

*This document is a living standard. As the architecture evolves, these rules must be updated to reflect the new enterprise baseline.*
