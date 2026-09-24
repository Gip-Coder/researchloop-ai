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

- **Member 1 (AI / Agent Engine)**: Core agent loop, prompt engineering, multi-provider retrieval (arXiv, Semantic Scholar, Crossref), deduplication, LLM reflection, benchmark comparisons, and frozen contract specification.
- **Member 2 (Application / Full-Stack Engineer)**: Complete application layer surrounding the engine:
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
pip install -r requirements.txt
```

Environment configuration:
```powershell
# Copy template (default runs zero-credential offline Mock Mode with local SQLite)
cp .env.example .env
```

To run with live providers, set in `.env`:
```ini
RESEARCHLOOP_MODE=live
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key-here
```

### 2. Frontend Setup

```powershell
cd frontend
npm install
npm run build
cd ..
```

---

## Running the Application

### Option A: Run Backend API & Static Frontend in One Process

When the frontend is built (`frontend/dist`), FastAPI automatically serves both the API and the single-page application:

```powershell
python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://localhost:8000` in your browser.

### Option B: Concurrent Development (FastAPI + Vite Hot Reload)

1. **Terminal 1 — Backend API:**
   ```powershell
   python -m uvicorn backend.api.main:app --port 8000 --reload
   ```

2. **Terminal 2 — Frontend Dev Server:**
   ```powershell
   cd frontend
   npm run dev
   ```

Open `http://localhost:3000` in your browser. All API requests are proxied automatically to `http://localhost:8000`.

---

## Primary API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/research` | Create & launch autonomous research loop in background |
| `GET` | `/api/research` | List historical research runs |
| `GET` | `/api/research/{id}` | Get status, coverage, and overview of a run |
| `GET` | `/api/research/{id}/iterations` | Get iterative loop audit logs & plans |
| `GET` | `/api/research/{id}/papers` | Query discovered papers with filters (`is_relevant`, `source`, `sort_by`, `search`) |
| `GET` | `/api/research/{id}/themes` | Get extracted thematic clusters |
| `GET` | `/api/research/{id}/events` | Get agent event trace and execution logs |
| `GET` | `/api/research/{id}/events/stream` | Server-Sent Events (SSE) live real-time stream |
| `GET` | `/api/research/{id}/result` | Get synthesized literature review & report |
| `GET` | `/api/research/{id}/evaluation` | Get intrinsic & benchmark evaluation metrics |
| `POST` | `/api/research/{id}/cancel` | Cancel an active research loop |
| `GET` | `/api/health` | Service health and operating mode |

Interactive Swagger documentation is available at `http://localhost:8000/docs`.

---

## Testing

All tests run **100% offline with zero external API credentials** by default.

### Backend Tests (API, Database, Services, Agent Engine)

```powershell
pytest tests/ -v
```

### Frontend Tests (Vitest & React Testing Library)

```powershell
cd frontend
npm test
```

### End-to-End Integration Test

Verifies `POST /api/research` $\to$ Background Runner $\to$ Real `ResearchEngine` in Mock Mode $\to$ Event persistence $\to$ Iteration 1 gap detection $\to$ Iteration 2 replanning $\to$ Multi-table persistence $\to$ `GET /api/research/{id}`:

```powershell
pytest tests/api/test_integration_e2e.py -v
```

---

## Demo Verification Scenario

Use the standard evaluation question:
```text
What are the current methods for factuality evaluation in retrieval-augmented generation?
```

The application demonstrates:
1. **Iteration 1**: Broad retrieval $\to$ 108 candidate papers $\to$ Relevance filtering $\to$ Thematic synthesis $\to$ Critic reflection flags missing standardized benchmarks (FactScore, RGB) at 65% coverage $\to$ Replanning.
2. **Iteration 2**: Targeted query retrieval $\to$ Benchmark integration $\to$ Critic satisfied at 90% coverage $\to$ Termination.
3. **Synthesis & Review**: Comprehensive narrative, structured themes, consensus findings, open gaps, and curated bibliography.
4. **Evaluation**: Intrinsic coherence, relevance precision, citation statistics, and curated ground-truth survey recall comparison.
