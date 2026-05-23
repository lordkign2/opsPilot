# OpsPilot - Project Scope

## AI Business Operations Assistant for SMEs

### Project Overview
**Working Title:** OpsPilot (placeholder)

OpsPilot is an AI-powered business operations platform designed for small and medium-sized enterprises (SMEs), particularly businesses that currently manage sales, customer communication, and operations manually through WhatsApp, phone calls, and handwritten records. 
The platform will serve as a digital operations manager, combining business automation, payment processing, customer management, real-time communication, and AI-powered decision support into a single system.

### Problem Statement
A large number of SMEs operate without structured digital systems for:
- Customer relationship management
- Sales tracking
- Order management
- Payment processing
- Business analytics
- Customer retention
- Operational automation

This leads to:
- Missed sales opportunities
- Poor record keeping
- Inefficient customer support
- Delayed payments
- Weak operational visibility

OpsPilot addresses these issues by centralizing core business workflows into one intelligent platform.

### Target Market
**Primary initial market:**
- Bakeries
- Printing presses
- Fashion vendors
- Recharge/data resellers
- Event vendors
- Local retail stores
- Service providers

**Geographic focus:**
- Nigerian SMEs, with expansion potential to other African markets.

### Core Features

#### 1. Authentication and Access Control
- Secure user registration and login
- Business workspace accounts
- Role-based permissions
- Staff management
- Roles include: Business owner, Manager, Cashier, Sales representative

#### 2. Customer Management Module
The platform will store and manage:
- Customer profiles
- Purchase history
- Contact information
- Interaction notes
- Tags and segmentation

**AI functionality:**
- Customer behavior analysis
- Re-engagement recommendations
- Sales opportunity detection

#### 3. Order Management System
Businesses can:
- Create orders manually
- Receive automated orders from integrated channels
- Track fulfillment stages
- Monitor delivery and completion status

**Capabilities:**
- Status tracking
- Live order updates
- Notifications
- Team collaboration

#### 4. Fintech and Payment Layer
Integrated payment infrastructure includes:
- Payment links
- Invoicing
- Transaction logs
- Revenue dashboards
- Wallet support

**Potential providers:** Paystack, Flutterwave

#### 5. AI Business Assistant
The AI engine will support:
- Automated customer replies
- Business insights generation
- Sales summaries
- Inventory recommendations
- Smart reminders
- Workflow automation

**Examples:** Detect abandoned orders, Recommend customer follow-up, Summarize daily sales performance, Predict stock shortages.

### Technical Architecture
**Frontend**
- Next.js
- Tailwind CSS
- shadcn/ui
- Framer Motion

**Backend**
- FastAPI
- PostgreSQL
- Redis
- WebSockets
- Celery workers
- Docker

**AI Layer**
- OpenAI APIs
- Embeddings
- Retrieval systems
- Event-driven automation

### System Design
Architecture layers:
- Client application
- Frontend dashboard
- API gateway
- Core backend services

Backend services include:
- Authentication service
- Customer service
- Order service
- Payment service
- AI service
- WebSocket service
- Analytics service

### Key Differentiators
OpsPilot combines multiple business-critical capabilities rarely available together for SMEs:
- Real-time operational monitoring
- AI-assisted decision making
- Integrated fintech workflows
- WhatsApp-first automation
- Scalable modular architecture
- Modern futuristic user experience

### WhatsApp Integration Strategy
A major strategic component is WhatsApp business automation.
**Workflow:**
- Customer sends message via WhatsApp
- AI interprets request
- Order is created automatically
- Payment link is generated
- Business owner receives instant alert
- Dashboard updates in real time
This aligns directly with current SME operational habits.

### Database Design
**Core entities:**
- `Business`: id, name, industry, subscription_plan
- `User`: id, business_id, role
- `Customer`: id, business_id, phone, notes
- `Order`: id, customer_id, amount, status
- `Payment`: id, order_id, provider, status
- `AIEvent`: id, business_id, event_type, payload

### Development Roadmap (30 Days)
- **Week 1 — Foundation**: Authentication system, Database setup, Business onboarding, Dashboard skeleton
- **Week 2 — Core Modules**: Customer management, Order management, Invoice generation, Basic analytics
- **Week 3 — Real-Time Features**: WebSocket implementation, Live notifications, Activity feed, Real-time updates
- **Week 4 — AI Layer**: AI assistant integration, Smart summaries, Automated reminders, Customer support chatbot

### Business Model
**Revenue Opportunities**
- Tier 1: Website only service
- Tier 2: Website + Operations Dashboard
- Tier 3: Website + Dashboard + AI Assistant

**Additional monetization:**
- Subscription plans
- Transaction fees
- Premium automation features
- Custom integrations

### Long-Term Vision
OpsPilot can evolve into a full SaaS ecosystem for African SMEs by expanding into:
- Inventory management
- Staff payroll
- Loan scoring
- Embedded finance
- AI accounting assistant
- Business credit systems
- Marketplace integrations

### Strategic Value
This project provides strong practical value because it:
- Solves a real operational problem
- Demonstrates advanced full-stack engineering
- Incorporates AI in meaningful workflows
- Supports fintech integrations
- Creates a sellable agency product
- Has startup scalability potential

### Conclusion
OpsPilot is a high-potential side project that combines real business utility with advanced technical depth. It is suitable as a production-ready portfolio project, a commercial SaaS startup MVP, an agency upsell product, or a long-term scalable business platform. Its strongest advantage is solving everyday business pain points while leveraging modern AI and real-time automation technologies.

---

## Backend Engineering Blueprint (Enterprise Architecture)

### Architectural Principles
- Clean Architecture
- Modular Monolith
- Domain-Driven Design (DDD-lite)
- Event-driven internal communication
- Async-first implementation

This provides scalability, maintainability, strong separation of concerns, and a future migration path to microservices.

### Recommended Backend Structure
```text
backend/
├── app/
│   ├── core/
│   ├── config/
│   ├── db/
│   ├── shared/
│   ├── modules/
│   │   ├── auth/
│   │   ├── businesses/
│   │   ├── customers/
│   │   ├── orders/
│   │   ├── payments/
│   │   ├── notifications/
│   │   ├── ai/
│   │   └── analytics/
│   ├── websocket/
│   └── main.py
├── tests/
├── migrations/
├── docker/
└── pyproject.toml
```

### Per-Module Layout
```text
module/
├── models.py
├── schemas.py
├── repository.py
├── service.py
├── routes.py
├── dependencies.py
└── events.py
```

### Responsibilities
- **models.py**: Database ORM entities.
- **schemas.py**: Pydantic validation models.
- **repository.py**: Database access abstraction.
- **service.py**: Business logic layer.
- **routes.py**: HTTP endpoints only.
- **dependencies.py**: Dependency injection.
- **events.py**: Internal event publishers and consumers.

### Required Technology Stack
- **Framework**: FastAPI
- **Database**: PostgreSQL, SQLAlchemy 2.0 (async), Alembic, asyncpg
- **Authentication**: python-jose, passlib, Authlib (optional OAuth)
- **Realtime and Background Processing**: Redis, Celery, WebSockets
- **AI**: OpenAI APIs, embeddings/vector store

### Core Modules Build Order
- **Phase 1**: core config, database setup, auth
- **Phase 2**: businesses, customers, orders, payments
- **Phase 3**: AI, notifications, analytics

### Recommended API Routes
- **Auth**: `/register`, `/login`, `/refresh`, `/logout`, `/me`
- **Businesses**: `/`, `/{id}`, `/current`
- **Customers**: `/`, `/{id}`, `/search`
- **Orders**: `/`, `/{id}`, `/status`
- **Payments**: `/`, `/webhook`, `/verify`, `/history`
- **AI**: `/chat`, `/summary`, `/recommendations`, `/customer-insights`

### Initial Database Tables
- **businesses**: id, name, industry, plan, created_at
- **users**: id, business_id, email, password_hash, role, created_at
- **customers**: id, business_id, name, phone, email, notes
- **orders**: id, customer_id, business_id, status, total_amount
- **payments**: id, order_id, provider, tx_ref, status
- **ai_logs**: id, business_id, event_type, payload

### Engineering Practices
**Mandatory Patterns**
- Service layer pattern
- Repository pattern
- Dependency injection
- Event-driven communication
- Centralized logging
- Structured configuration

**Dev Tooling**
- Ruff, Black, mypy, Pytest

**Docker Services**
- backend, postgres, redis, celery_worker, celery_beat, nginx
