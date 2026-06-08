<div align="center">

<!-- Hero Banner -->
<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:0f0f23,50:1a1a3e,100:0d1117&height=200&section=header&text=DeepFeed%20AI&fontSize=64&fontColor=6ee7f7&fontAlignY=40&desc=Discover%20Signal.%20Ignore%20Noise.&descSize=20&descAlignY=65&descColor=a78bfa" />

<!-- Status Badges -->
[![Build Status](https://img.shields.io/github/actions/workflow/status/yourusername/deepfeed-ai/ci.yml?branch=main&style=for-the-badge&logo=github-actions&logoColor=white&color=22c55e&labelColor=0f0f23)](https://github.com/yourusername/deepfeed-ai/actions)
[![Tests](https://img.shields.io/badge/tests-123%20passing-22c55e?style=for-the-badge&logo=pytest&logoColor=white&labelColor=0f0f23)](https://github.com/yourusername/deepfeed-ai)
[![Coverage](https://img.shields.io/badge/coverage-80%25+-6ee7f7?style=for-the-badge&logo=codecov&logoColor=white&labelColor=0f0f23)](https://github.com/yourusername/deepfeed-ai)
[![Python](https://img.shields.io/badge/python-3.12-a78bfa?style=for-the-badge&logo=python&logoColor=white&labelColor=0f0f23)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-f59e0b?style=for-the-badge&labelColor=0f0f23)](LICENSE)

<br/>

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+pgvector-336791?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-agentic-ff6b6b?style=flat-square&logo=langchain&logoColor=white)](https://langchain.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-enabled-f97316?style=flat-square&logo=opentelemetry&logoColor=white)](https://opentelemetry.io)

<br/><br/>

> **DeepFeed AI** is a production-grade, AI-powered personalized knowledge discovery platform.  
> It cuts through information overload — surfacing what matters to *you*, and silencing what doesn't.

<br/>

[**Get Started**](#-quick-start) · [**Architecture**](#-architecture) · [**API Docs**](#-api-reference) · [**Contributing**](#-contributing)

</div>

---

## 📖 Table of Contents

- [✨ Features](#-features)
- [🏗 Architecture](#-architecture)
- [🧰 Tech Stack](#-tech-stack)
- [🗂 Project Structure](#-project-structure)
- [🚀 Quick Start](#-quick-start)
- [⚙️ Configuration](#-configuration)
- [🔄 AI Development Workflow](#-ai-development-workflow)
- [🧪 Testing](#-testing)
- [📊 Observability](#-observability)
- [🔒 Security](#-security)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🔍 Discovery Pipeline
- Multi-source content ingestion (RSS, APIs, web scraping)
- Real-time signal extraction and topic classification
- Semantic deduplication via pgvector embeddings
- Configurable freshness and quality scoring

</td>
<td width="50%">

### 🤖 Agentic Adaptation
- LangGraph-powered research agent microservice
- Background job execution with priority queuing
- Self-evaluating research workflows (V6.9+)
- Pluggable LLM router (Anthropic · OpenAI · Gemini)

</td>
</tr>
<tr>
<td width="50%">

### 🎯 Recommendation Engine
- User preference modeling with continuous feedback loops
- Collaborative + content-based hybrid ranking
- Personalization scoring per item per user
- Cold-start handling for new users

</td>
<td width="50%">

### 🏭 Production-Ready
- Full observability: Prometheus + Grafana + OTel tracing
- Async task processing via Celery + RabbitMQ
- JWT authentication with Argon2 password hashing
- Docker Compose deployment with Nginx reverse proxy

</td>
</tr>
</table>

---

## 🏗 Architecture

DeepFeed AI follows a **Modular Monolith + Event-Driven Processing + Agentic Adaptation Layer** architecture.

```
╔══════════════════════════════════════════════════════════════════════════╗
║                         DeepFeed AI Platform                             ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │                      Next.js 14 Frontend                        │   ║
║   │           TypeScript · TailwindCSS · TanStack Query             │   ║
║   └──────────────────────────┬──────────────────────────────────────┘   ║
║                              │ HTTPS / REST                              ║
║                              ▼                                           ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │                    Nginx Reverse Proxy                          │   ║
║   └──────────────────────────┬──────────────────────────────────────┘   ║
║                              │                                           ║
║                              ▼                                           ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │                   FastAPI Application Core                      │   ║
║   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │   ║
║   │  │   Auth   │  │ Discovery│  │  Reco.   │  │   Agentic     │  │   ║
║   │  │ Module   │  │ Pipeline │  │  Engine  │  │  Adaptation   │  │   ║
║   │  └──────────┘  └──────────┘  └──────────┘  └───────────────┘  │   ║
║   │  ┌──────────────────────────────────────────────────────────┐  │   ║
║   │  │              Application Service Layer                    │  │   ║
║   │  └──────────────────────────────────────────────────────────┘  │   ║
║   └───────┬────────────────────┬──────────────────────┬────────────┘   ║
║           │                    │                      │                  ║
║           ▼                    ▼                      ▼                  ║
║   ┌──────────────┐   ┌──────────────────┐   ┌──────────────────────┐   ║
║   │ PostgreSQL 16│   │  Celery Workers  │   │  Research Agent      │   ║
║   │  + pgvector  │   │  + RabbitMQ      │   │  Microservice        │   ║
║   │              │   │                  │   │  (LangGraph)         │   ║
║   └──────────────┘   └──────────────────┘   └──────────────────────┘   ║
║                                                                          ║
║   ┌──────────────────────────────────────────────────────────────────┐  ║
║   │         Observability Stack                                      │  ║
║   │   Prometheus · Grafana · OpenTelemetry · Structlog               │  ║
║   └──────────────────────────────────────────────────────────────────┘  ║
╚══════════════════════════════════════════════════════════════════════════╝
```

### Event Flow

```
Content Sources          Platform Core            User Layer
─────────────          ─────────────            ──────────
     │                       │                       │
     │  Ingest               │                       │
     ├──────────────────────►│                       │
     │                       │  Score & Rank         │
     │                       ├──────────────────────►│
     │                       │                       │  Feedback
     │                       │◄──────────────────────┤
     │                  Event Bus                    │
     │                  (RabbitMQ)                   │
     │                       │                       │
     │                  Celery Worker                │
     │                  (async tasks)                │
     │                       │                       │
     │               Research Agent                  │
     │               (LangGraph / OTel)              │
```

### Module Boundaries

```
┌──────────────────────────────────────────────────┐
│  Allowed Dependency Direction: ──►               │
│                                                  │
│  API Layer                                       │
│      ──► Application Services                   │
│              ──► Domain Models                  │
│              ──► Infrastructure (DB, Queue)     │
│                                                  │
│  ✗  Infrastructure must NOT import App Services │
│  ✗  Domain must NOT import Infrastructure       │
└──────────────────────────────────────────────────┘
```

---

## 🧰 Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Next.js 14 · TypeScript · TailwindCSS | UI / UX |
| **API** | FastAPI · Python 3.12 · Pydantic v2 | REST API |
| **ORM** | SQLAlchemy 2.0 async · Alembic | Database access & migrations |
| **Database** | PostgreSQL 16 + pgvector | Primary store + semantic search |
| **Cache** | Redis | Session, rate-limiting, short-lived state |
| **Queue** | RabbitMQ + Celery | Async task execution |
| **AI Agents** | LangGraph · LangChain | Agentic research workflows |
| **LLM Router** | Anthropic · OpenAI · Gemini | Pluggable LLM providers |
| **Auth** | JWT + Argon2 | Authentication & password hashing |
| **Infra** | Docker Compose · Nginx | Container orchestration |
| **CI/CD** | GitHub Actions | Automated testing & deployment |
| **Observability** | Prometheus · Grafana · OpenTelemetry · Structlog | Metrics, tracing, logging |

---

## 🗂 Project Structure

```
deepfeed-ai/
├── 📁 backend/                    # FastAPI application
│   ├── app/
│   │   ├── api/                   # Route handlers
│   │   ├── core/                  # Config, security, dependencies
│   │   ├── modules/
│   │   │   ├── auth/              # Authentication & authorization
│   │   │   ├── discovery/         # Content ingestion pipeline
│   │   │   ├── recommendation/    # Ranking & personalization
│   │   │   └── agentic/           # Agentic adaptation layer
│   │   ├── services/              # Application service layer
│   │   ├── models/                # SQLAlchemy ORM models
│   │   └── workers/               # Celery task definitions
│   ├── alembic/                   # Database migrations
│   └── tests/                     # Unit + integration tests
│
├── 📁 frontend/                   # Next.js 14 application
│   ├── src/
│   │   ├── app/                   # App router pages
│   │   ├── components/            # Reusable UI components
│   │   ├── hooks/                 # TanStack Query hooks
│   │   └── lib/                   # API client, utilities
│   └── tests/                     # E2E + component tests
│
├── 📁 research-agent/             # LangGraph microservice
│   ├── agent/
│   │   ├── graph/                 # LangGraph workflow definitions
│   │   ├── nodes/                 # Agent node implementations
│   │   ├── evaluation/            # Research eval framework (V6.9)
│   │   └── jobs/                  # Background job execution (V6.7/6.8)
│   └── tests/                     # 111 passing tests
│
├── 📁 deployment/
│   └── docker/
│       ├── docker-compose.yml
│       ├── docker-compose.prod.yml
│       └── nginx/
│
├── 📁 .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
│
└── 📄 README.md
```

---

## 🚀 Quick Start

### Prerequisites

Ensure you have the following installed:

```bash
# Required
docker --version        # 24.0+
docker compose version  # 2.20+
python --version        # 3.12+
node --version          # 20+
```

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/deepfeed-ai.git
cd deepfeed-ai
```

### 2. Configure Environment

```bash
# Copy environment templates
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
cp research-agent/.env.example research-agent/.env

# Edit with your values (API keys, DB credentials, etc.)
# Minimum required: ANTHROPIC_API_KEY, POSTGRES_PASSWORD, SECRET_KEY
nano backend/.env
```

### 3. Start with Docker Compose

```bash
# From the project root
cd deployment/docker
docker compose up --build

# Or in detached mode
docker compose up -d --build
```

### 4. Run Migrations

```bash
docker compose exec backend alembic upgrade head
```

### 5. Access the Platform

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **API Docs (ReDoc)** | http://localhost:8000/redoc |
| **Grafana Dashboard** | http://localhost:3001 |
| **Prometheus** | http://localhost:9090 |
| **RabbitMQ Management** | http://localhost:15672 |

### Local Development (Without Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Research Agent
cd research-agent
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Celery Worker
cd backend
celery -A app.workers.celery_app worker --loglevel=info
```

---

## ⚙️ Configuration

Key environment variables:

```env
# ── Database ──────────────────────────────────────
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=deepfeed
POSTGRES_USER=deepfeed
POSTGRES_PASSWORD=your_secure_password

# ── Auth ──────────────────────────────────────────
SECRET_KEY=your_jwt_secret_minimum_32_chars
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ── LLM Providers (at least one required) ─────────
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AI...

# ── Queue ─────────────────────────────────────────
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
REDIS_URL=redis://localhost:6379/0

# ── Observability ─────────────────────────────────
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
LOG_LEVEL=INFO
```

---

## 🔄 AI Development Workflow

This project follows a disciplined AI-assisted development process. All AI coding agents must adhere to the following:

```
┌─────────────────────────────────────────────────────┐
│              AI Development Lifecycle                 │
│                                                       │
│  1. READ MILESTONE                                    │
│        ↓                                             │
│  2. READ TDS SECTION                                  │
│        ↓                                             │
│  3. IDENTIFY AFFECTED MODULES & ADRs                  │
│        ↓                                             │
│  4. EXPLAIN IMPLEMENTATION PLAN                       │
│        ↓                                             │
│  5. GENERATE CODE                                     │
│     • Follow repository structure                     │
│     • Follow module boundaries                        │
│     • Include type hints + error handling             │
│     • Include structured logging (structlog)          │
│     • Include OTel tracing                            │
│        ↓                                             │
│  6. GENERATE TESTS                                    │
│     • Unit tests                                      │
│     • Integration tests                               │
│     • Target: 80%+ coverage                          │
│        ↓                                             │
│  7. RUN REVIEW PROMPT                                 │
│     • Architecture compliance check                   │
│     • Security scan                                   │
│     • Performance review                              │
│        ↓                                             │
│  8. FIX ISSUES → COMMIT                               │
└─────────────────────────────────────────────────────┘
```

### Architecture Guardrails

> ⚠️ **These rules are enforced on every contribution — human or AI.**

| Rule | Status |
|------|--------|
| Uses defined modules only | ✅ Required |
| Uses application service layer | ✅ Required |
| Uses structured logging (structlog) | ✅ Required |
| Includes tests | ✅ Required |
| Uses dependency injection | ✅ Required |
| Includes error handling (AppError envelopes) | ✅ Required |
| Emits events where required | ✅ Required |
| Preserves architecture decisions | ✅ Required |
| Introduces new databases | ❌ Forbidden |
| Introduces microservices (outside research-agent) | ❌ Forbidden |
| Bypasses service boundaries | ❌ Forbidden |
| Invents requirements | ❌ Forbidden |

---

## 🧪 Testing

### Run All Tests

```bash
# Backend
cd backend
pytest --cov=app --cov-report=html -v

# Research Agent (111 tests)
cd research-agent
pytest --anyio-mode=auto -v

# Frontend
cd frontend
npm run test        # Unit + component
npm run test:e2e    # E2E with Playwright
```

### Test Coverage Targets

```
Module                    Coverage
─────────────────────────────────────
auth/                     ████████████ 92%
discovery/                ███████████░ 87%
recommendation/           ██████████░░ 82%
agentic/                  ██████████░░ 80%
research-agent/           ████████████ 91%
─────────────────────────────────────
Overall                   ██████████░░ 86%
```

### Test Structure

```
tests/
├── unit/           # Pure function, service logic
├── integration/    # DB, queue, external service integration
└── e2e/            # Full user journey (Playwright)
```

Conventions used in the research-agent service:
- `@pytest.mark.anyio` for all async tests
- `AppError` envelope assertions for error cases
- Negative-control seed datasets for evaluation CI robustness

---

## 📊 Observability

DeepFeed AI ships with a full observability stack out of the box.

```
Request ──► FastAPI ──► OpenTelemetry SDK
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
              Jaeger/Tempo          Prometheus
              (Distributed         (Metrics
               Tracing)             Scraping)
                    │                    │
                    └─────────┬──────────┘
                              ▼
                           Grafana
                         (Dashboards)
```

### Metrics Exposed

| Metric | Description |
|--------|-------------|
| `deepfeed_requests_total` | Total API requests by route + status |
| `deepfeed_discovery_items_ingested` | Items ingested per source |
| `deepfeed_recommendation_latency_seconds` | Ranking latency histogram |
| `deepfeed_agent_job_duration_seconds` | Research job execution time |
| `deepfeed_celery_task_failures_total` | Worker failure rate |

### Structured Log Format

All logs use `structlog` with JSON output:

```json
{
  "timestamp": "2026-01-15T10:23:45Z",
  "level": "info",
  "event": "recommendation.generated",
  "user_id": "usr_abc123",
  "items_ranked": 42,
  "latency_ms": 87,
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
}
```

---

## 🔒 Security

| Feature | Implementation |
|---------|---------------|
| Password hashing | Argon2id (memory-hard) |
| Authentication | JWT (access + refresh tokens) |
| Authorization | Role-based, per-route |
| Input validation | Pydantic v2 strict mode |
| SQL injection | SQLAlchemy parameterized queries only |
| Secrets management | Environment variables, never hardcoded |
| API rate limiting | Redis-backed sliding window |
| CORS | Strict allowlist |

---

## 📋 Implementation Roadmap

```
Phase 1 — Foundation          ██████████ Done
Phase 2 — Core Platform       ██████████ Done
Phase 3 — Discovery Pipeline  ██████████ Done
Phase 4 — Recommendation      ██████████ Done
Phase 5 — Agentic Adaptation  ██████████ Done
Phase 6 — Production Ready    ██████████ Done

Research Agent V6.7  (Background Jobs)         ██████████ Done
Research Agent V6.8  (Heavy-Work Execution)    ██████████ Done
Research Agent V6.9  (Evaluation Framework)   ██████████ Done
Research Agent V6.10+ (Future milestones)      ░░░░░░░░░░ Planned
```

---

## 🤝 Contributing

Contributions are welcome. Please read the AI Development Prompt Pack before opening a PR — all code (human and AI-generated) must pass the Architecture Compliance Checklist.

```bash
# 1. Fork and clone
git clone https://github.com/yourusername/deepfeed-ai.git

# 2. Create a feature branch
git checkout -b feat/your-feature-name

# 3. Implement following the AI Development Workflow above

# 4. Ensure tests pass
pytest && npm run test

# 5. Open a pull request with:
#    - Milestone ID implemented
#    - Affected modules listed
#    - Architecture compliance confirmed
```

### Commit Convention

```
feat(module):  short description
fix(module):   short description
test(module):  short description
docs:          short description
refactor:      short description
```

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,50:1a1a3e,100:0f0f23&height=100&section=footer" />

**Built with precision. Driven by signal.**

[![GitHub Stars](https://img.shields.io/github/stars/yourusername/deepfeed-ai?style=social)](https://github.com/yourusername/deepfeed-ai)
[![GitHub Forks](https://img.shields.io/github/forks/yourusername/deepfeed-ai?style=social)](https://github.com/yourusername/deepfeed-ai/fork)

</div>
