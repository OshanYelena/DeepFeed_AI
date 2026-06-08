# DeepFeed AI

> **Discover signal. Ignore noise.**

DeepFeed AI is an adaptive knowledge intelligence platform that automatically discovers, evaluates, and personalizes technical content — learning from your behavior over time.

---

## Architecture

```
Modular Monolith + Event-Driven Processing + Agentic Adaptation Layer
```

**Stack:**
- **Backend:** FastAPI, Python 3.12, SQLAlchemy 2.0, Alembic, Celery
- **Frontend:** Next.js 14, TypeScript, TailwindCSS, TanStack Query
- **Database:** PostgreSQL 16 + pgvector
- **Queue:** RabbitMQ
- **Observability:** Prometheus, Grafana, OpenTelemetry
- **AI:** Anthropic Claude, OpenAI GPT, Google Gemini (pluggable)

---

## Project Structure

```
deepfeed-ai/
├── apps/
│   ├── backend/
│   │   ├── api/              # FastAPI routes, middleware, dependencies
│   │   ├── application/      # Application services, DTOs, agents
│   │   ├── domain/           # Events, interfaces, domain models
│   │   ├── infrastructure/   # DB, auth, LLM, providers, observability
│   │   ├── workers/          # Celery tasks and scheduler
│   │   ├── tests/            # Unit, integration, E2E tests
│   │   └── prompts/          # Versioned LLM prompt templates
│   └── frontend/
│       └── src/
│           ├── app/          # Next.js App Router pages
│           ├── components/   # UI, feed, auth, profile components
│           ├── lib/          # API client, auth store
│           └── types/        # TypeScript types
├── deployment/
│   ├── docker/               # Dockerfiles, compose, DB init
│   ├── nginx/                # Reverse proxy config
│   └── monitoring/           # Prometheus, Grafana dashboards
├── docs/
└── .github/workflows/        # CI/CD pipeline
```

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- (Optional) OpenAI or Anthropic API key

### 1. Clone and configure

```bash
git clone <repo>
cd deepfeed-ai
cp apps/backend/.env apps/backend/.env
# Edit .env and add your LLM API keys
```

### 2. Start all services

```bash
cd deployment/docker
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- RabbitMQ (port 5672, management UI: 15672)
- Backend API (port 8000)
- Celery Worker + Beat scheduler
- Frontend (port 3000)
- Nginx (port 80)
- Prometheus (port 9090)
- Grafana (port 3001, admin/deepfeed)

### 3. Run database migrations

```bash
docker exec deepfeed_backend alembic upgrade head
```

### 4. Seed initial data

```bash
docker exec deepfeed_backend python seed.py
```

Admin credentials: `admin@deepfeed.ai` / `AdminDeepFeed123!`

### 5. Access the app

| Service      | URL                    |
|-------------|------------------------|
| Frontend     | http://localhost:3000  |
| Backend API  | http://localhost:8000  |
| API Docs     | http://localhost:8000/docs |
| Grafana      | http://localhost:3001  |
| RabbitMQ UI  | http://localhost:15672 |

---

## Development

### Backend

```bash
cd apps/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Run tests

```bash
cd apps/backend
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v
```

### Celery worker

```bash
cd apps/backend
celery -A workers.celery_app worker --loglevel=info
```

### Frontend

```bash
cd apps/frontend
npm install
npm run dev
```

---

## Implementation Roadmap Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 0 | Foundation (FastAPI, Next.js, Docker, CI) | ✅ Complete |
| Phase 1 | Core Platform (Auth M1, Profile M2, Interests M3) | ✅ Complete |
| Phase 2 | Discovery Pipeline (Sources M4, RSS M5, arXiv M6, Processing M7) | ✅ Complete |
| Phase 3 | Recommendation System (Ranking M8, Feed M9, Summarization M10) | ✅ Complete |
| Phase 4 | Agentic Adaptation (Signals M11, UserModeling M12, Research M13, Reflection M14, Engine M15) | ✅ Complete |
| Phase 5 | Production Readiness (Observability M16, Security M17, Performance M18, Testing M19) | ✅ Complete |
| Phase 6 | Future Intelligence (Learning-to-Rank, Bandits, Knowledge Graph) | 🔜 Future |

---

## Ranking Formula

```
Final Score = Relevance × 0.40 + Credibility × 0.20 + Freshness × 0.15 + Novelty × 0.15 + Feedback × 0.10
```

---

## Agentic Loop

```
Observe → Interpret → Decide → Act → Learn
```

Agents:
- **User Modeling Agent** — learns topic/source preferences from behavior
- **Research Planning Agent** — generates personalized search plans
- **Reflection Agent** — analyzes performance and generates improvement insights
- **Adaptation Engine** — orchestrates all agents in a full cycle

---

## API Overview

| Endpoint | Description |
|----------|-------------|
| `POST /auth/register` | Register user |
| `POST /auth/login` | Login, get JWT |
| `GET /profile/me` | Get profile |
| `PUT /profile/me` | Update preferences |
| `GET/POST /interests` | Manage interests |
| `GET /feed` | Personalized feed |
| `POST /feedback` | Submit feedback |
| `GET /agent/profile-insights` | Learned preferences |
| `POST /agent/adapt/run` | Run adaptation cycle |
| `GET /agent/reflection/latest` | Latest reflection |
| `GET /health/ready` | Readiness check |
| `GET /metrics` | Prometheus metrics |

---

## Architecture Principles (enforced)

1. **No microservices** — Modular Monolith only
2. **No direct DB from agents** — All writes through application services
3. **Every recommendation has a trace** — RecommendationTrace for explainability
4. **Every adaptation has an event** — AdaptationEvent for traceability
5. **Deterministic pipeline + Agentic layer separated** — Clear boundary
6. **All adaptation flows through services** — Never bypass business logic
