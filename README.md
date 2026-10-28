# researchloop-ai

**An agentic AI pipeline for autonomous literature review with iterative planning, retrieval, synthesis, and self-reflection.**

---

## System Architecture

```text
Frontend (React 18 + TypeScript + Vite)
       ↓  (HTTP REST / SSE Event Streams)
FastAPI Application Layer (`backend/api/`)
       ↓
Application Services (`ResearchService` & `ResearchRunner`)
       ↓
AI Research Engine (`backend/agent/orchestration/engine.py`)
       ↓
Multi-Agent Loop: Planning → Retrieval → Deduplication → Relevance → Synthesis → Critic → Replanning
       ↓
Persistence Layer (SQLAlchemy ORM + SQLite/PostgreSQL)
       ↓
Frontend Visualization (Dashboard, Trace, Papers, Themes, Gaps, Review, Evaluation)
```

---

## Team Division of Responsibilities

- **Member 1 (AI / Agent Engine)**: Core agent loop, prompt engineering, multi-provider retrieval (arXiv, Semantic Scholar, Crossref), deduplication, LLM reflection, benchmark comparisons, and frozen contract specification ([`docs/AGENT_ENGINE_CONTRACT.md`](docs/AGENT_ENGINE_CONTRACT.md)).
- **Member 2 (Application / Full-Stack Engineer)**: Complete application layer surrounding the engine ([`docs/APPLICATION_LAYER_GUIDE.md`](docs/APPLICATION_LAYER_GUIDE.md)):
  - Asynchronous SQLAlchemy persistence (`backend/database/`, `backend/repositories/`)
  - Background orchestrator with real-time SSE telemetry streams (`backend/services/`)
  - Clean RESTful FastAPI endpoints with DTO schemas and validation (`backend/api/`)
  - Academic research user interface (`frontend/`)
  - Comprehensive unit, integration, and end-to-end test suite (`tests/api/`, `tests/database/`, `tests/services/`, `frontend/src/test/`)

---

## Quickstart & Installation

### 1. Backend Setup

```powershell
# Install backend Python dependencies
python -m pip install -r requirements.txt
```

Environment configuration:
```powershell
# Copy template (default runs zero-credential offline Mock Mode with local SQLite)
cp .env.example .env
```

### Environment Variables Reference

| Variable | Default | Description |
| :--- | :--- | :--- |
| `RESEARCHLOOP_MODE` | `mock` | `'mock'` (offline deterministic fixtures) or `'live'` (real APIs) |
| `LLM_PROVIDER` | `mock` | `'mock'`, `'openai'`, `'anthropic'`, `'gemini'`, or `'ollama'` |
| `LLM_MODEL` | *(provider default)* | Optional override (e.g. `gpt-4o-mini`, `gemini-3.8-flash`, `llama3.2:3b`) |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Local Ollama API URL |
| `OPENAI_API_KEY` | *(empty)* | Required when `LLM_PROVIDER=openai` |
| `ANTHROPIC_API_KEY` | *(empty)* | Required when `LLM_PROVIDER=anthropic` |
| `GEMINI_API_KEY` | *(empty)* | Required when `LLM_PROVIDER=gemini` |
| `SEMANTIC_SCHOLAR_API_KEY` | *(empty)* | Optional API key for higher Semantic Scholar rate limits |
| `CROSSREF_MAILTO` | `researcher@example.com` | Polite pool contact email for Crossref API |
| `DATABASE_URL` | `sqlite+aiosqlite:///./researchloop.db` | Async SQLAlchemy URL (SQLite default; supports `postgresql+asyncpg://...`) |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:5173,...` | Comma-separated CORS allowed origins |

To run with live providers, set in `.env`:
```ini
RESEARCHLOOP_MODE=live
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key-here
```

For a local Ollama model, install Ollama, pull a model with `ollama pull llama3.2:3b`, then set:
```ini
RESEARCHLOOP_MODE=live
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

### 2. Frontend Setup

```powershell
cd frontend
npm install
npm run build
cd ..
```

### 3. Database Initialization

Database tables (`research_runs`, `research_iterations`, `papers`, `research_run_papers`, `themes`, `agent_events`) are automatically initialized on FastAPI application startup via `init_db()` (`Base.metadata.create_all`). No manual migration step is required for fresh SQLite or PostgreSQL instances.

---

## Running the Application

### Option A: Run Backend API & Static Frontend in One Process

When the frontend is built (`frontend/dist`), FastAPI automatically serves both the API and the single-page application:

```powershell
python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://127.0.0.1:8000` in your browser.

### Option B: Concurrent Development (FastAPI + Vite Hot Reload)

1. **Terminal 1 — Backend API:**
   ```powershell
   python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. **Terminal 2 — Frontend Dev Server:**
   ```powershell
   cd frontend
   npm run dev
   ```

Open `http://127.0.0.1:5173` in your browser. All `/api` requests are proxied automatically to `http://127.0.0.1:8000`.

### Option C: Standalone Agent Engine CLI (Mock or Live)

```powershell
python -m backend.agent.cli "What are the current methods for factuality evaluation in retrieval-augmented generation?" --mock
```

---

## Primary API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/research` | Create & launch autonomous research loop in background |
| `GET` | `/api/research` | List historical research runs |
| `GET` | `/api/research/{id}` | Get status, coverage, and overview of a run |
| `GET` | `/api/research/{id}/iterations` | Get iterative loop audit logs & plans |
| `GET` | `/api/research/{id}/papers` | Query discovered papers with filters (`is_relevant`, `source`, `min_relevance`, `sort_by`, `search`) |
| `GET` | `/api/research/{id}/themes` | Get extracted thematic clusters |
| `GET` | `/api/research/{id}/events` | Get agent event trace and execution logs |
| `GET` | `/api/research/{id}/events/stream` | Server-Sent Events (SSE) live real-time stream |
| `GET` | `/api/research/{id}/result` | Get synthesized literature review & report |
| `GET` | `/api/research/{id}/evaluation` | Get intrinsic & benchmark evaluation metrics |
| `POST` | `/api/research/{id}/cancel` | Cancel an active research loop |
| `GET` | `/api/health` | Service health and operating mode |

Interactive Swagger documentation is available at `http://127.0.0.1:8000/docs`.

---

## Testing

All standard tests run **100% offline with zero external API credentials** by default.

### Backend Tests (API, Database, Services, Agent Engine)

```powershell
python -m pytest tests/ -v
```

### Frontend Tests & Build Verification (Vitest & TypeScript)

```powershell
cd frontend
npm test
npm run build
```

### End-to-End Integration Test

Verifies `POST /api/research` $\to$ Background Runner $\to$ Real `ResearchEngine` in Mock Mode $\to$ Event persistence $\to$ Iteration 1 gap detection $\to$ Iteration 2 replanning $\to$ Multi-table persistence $\to$ `GET /api/research/{id}`:

```powershell
python -m pytest tests/api/test_integration_e2e.py -v
```

---

## Demo Verification Scenario

Use the standard evaluation question:
```text
What are the current methods for factuality evaluation in retrieval-augmented generation?
```

The application demonstrates:
1. **Iteration 1**: Broad retrieval $\to$ 108 candidate papers $\to$ Deduplication (8 unique) & relevance filtering (7 relevant) $\to$ Thematic synthesis $\to$ Critic reflection flags missing standardized benchmarks (FactScore, RGB) at 65% coverage $\to$ Replanning.
2. **Iteration 2**: Targeted query retrieval $\to$ Benchmark integration $\to$ Critic satisfied at 90% coverage $\to$ Termination (`target_coverage_reached`).
3. **Synthesis & Review**: Comprehensive narrative, structured themes, consensus findings, open gaps, and curated bibliography with Markdown export.
4. **Evaluation**: Intrinsic coherence (`1.00`), relevance precision (`0.89`), citation statistics, and curated ground-truth survey recall comparison (`100%` key paper recall).

---

## Troubleshooting & Known Limitations

- **`pytest` not recognized on Windows PowerShell**: Run `python -m pytest tests/ -v` to invoke pytest via your active Python interpreter.
- **Port binding (`EACCES`) on Windows**: Vite is pre-configured to bind to `127.0.0.1:5173` (`frontend/vite.config.ts`). For Uvicorn, specify `--host 127.0.0.1 --port 8000`.
- **Single-process task & SSE state**: Active background tasks and SSE queues are stored in process memory; run Uvicorn with a single worker process for local/single-node deployments.
- **Audit & Verification Documentation**:
  - [`docs/PROJECT_AUDIT.md`](docs/PROJECT_AUDIT.md) — Complete functionality inventory, defects found, and fixes applied
  - [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md) — Test suite execution report
  - [`docs/SECURITY_AUDIT.md`](docs/SECURITY_AUDIT.md) — Security review and prompt-injection defenses
  - [`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md) — Known limitations and external dependencies
