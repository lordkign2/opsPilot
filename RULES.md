# OpsPilot Architectural Rules & Engineering Standards

**Author:** Principal Software Engineer & Architecture Review Lead  
**Scope:** `opspilot-backend` (FastAPI / Async SQLAlchemy)  
**Status:** ENFORCED  

This document outlines the architectural patterns, engineering standards, and security requirements for the OpsPilot backend. It is the definitive guide for how code is written in this repository. Rules are non-negotiable unless explicitly waived by an Architecture Review.

---

## 1. Core Architecture & Layering

### 1.1 Strict Layering
**[REQUIRED]** The application enforces a strict three-tier architecture: Router → Service → Repository. 
- **Routers** handle HTTP concerns (parsing, validation, response formatting).
- **Services** contain business logic, orchestration, and event emission.
- **Repositories** handle database interactions.

**[PROHIBITED]** Do not inject database sessions (`AsyncSession`) directly into routers. Do not write business logic or execute queries in the routing layer.

### 1.2 Centralised Registration
**[OBSERVED]** The application uses `app.core.registry.py` to mount all module routers and event handlers.
**[REQUIRED]** Do not modify `main.py` when adding a new module. All new module routers MUST be registered in `app.core.registry`.

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

## 3. Security & Authentication

### 3.1 Token Invalidation
**[OBSERVED]** Redis is used to blacklist JWTs upon logout.
**[REQUIRED]** Every state-changing authentication event (logout, password change) MUST blacklist the current tokens in Redis. 

### 3.2 Secret Management
**[DEBT]** Passwords and secrets are currently typed as standard `str` in `app.core.config.py`.
**[RECOMMENDED]** Migrate sensitive configuration fields (e.g., `JWT_SECRET_KEY`, `DATABASE_URL`) to Pydantic's `SecretStr` to prevent accidental logging or exposure in memory dumps.

### 3.3 Password Hashing
**[REQUIRED]** All password hashes MUST use the centralised `hash_password` and `verify_password` utilities in `app.core.security`. Custom crypto implementations are forbidden.

---

## 4. Error Handling & Responses

### 4.1 Response Envelopes
**[OBSERVED]** A unified response format exists in `app.shared.response.py`.
**[REQUIRED]** All successful API responses MUST be wrapped using `success_response` or `paginated_response`. 
**[PROHIBITED]** Do not return raw Pydantic models, dicts, or lists directly from route handlers.

### 4.2 Exception Management
**[OBSERVED]** A custom exception hierarchy descends from `OpsPilotException` in `app.core.exceptions`.
**[REQUIRED]** Raise specific domain exceptions (e.g., `NotFoundError`, `UnauthorizedError`). The global exception handler will automatically translate these into standard JSON error envelopes.
**[DANGEROUS]** Do not catch generic `Exception` objects in business logic without re-raising, as it masks underlying system failures and prevents the global error handler from logging them correctly.
**[PROHIBITED]** Never return `JSONResponse` manually with 4xx/5xx status codes from a router or service. Always raise an exception.

---

## 5. Observability & Auditing

### 5.1 Logging Discipline
**[REQUIRED]** Use the application logger (`get_logger(__name__)`).
**[PROHIBITED]** The use of `print()` statements for debugging or output is banned in production code.

### 5.2 Event-Driven Side Effects
**[OBSERVED]** An asynchronous event bus exists (`app.core.events`).
**[RECOMMENDED]** Use the event bus for all non-critical side effects (e.g., sending welcome emails, triggering analytics). Do not block the primary HTTP request lifecycle for these tasks.

---

## 6. API Design Standards

### 6.1 Pagination
**[REQUIRED]** Any endpoint returning a list of resources MUST support pagination (`offset`, `limit`). Do not execute unbounded `SELECT *` queries.

### 6.2 Naming Conventions
**[REQUIRED]** Endpoints must follow RESTful plural noun conventions (e.g., `/api/v1/businesses`, not `/api/v1/getBusiness`).
**[REQUIRED]** Database schemas must use `snake_case` column names and `plural` table names.

---

*This document is a living standard. As the architecture evolves, these rules must be updated to reflect the new enterprise baseline.*
