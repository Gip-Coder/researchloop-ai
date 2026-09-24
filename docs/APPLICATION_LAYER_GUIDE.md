# Application Layer & Full-Stack Integration Guide (Member 2)

**Author:** Member 2 (Application / Full-Stack Engineer)  
**Contract Reference:** [`docs/AGENT_ENGINE_CONTRACT.md`](AGENT_ENGINE_CONTRACT.md)  
**Version:** `1.0.0`

---

## 1. Architectural Architecture

The application layer builds an asynchronous, persistent web product around Member 1's frozen agent engine:

```text
┌────────────────────────────────────────────────────────┐
│                   Frontend (React 18)                  │
│  - ResearchForm (inquiry input & parameter config)    │
│  - DashboardHeader (status, iteration, coverage bar)   │
│  - LiveProgress (real-time streaming agent checkmarks) │
│  - AgentTimeline (collapsible decision trace)          │
│  - PaperExplorer (search, filter, sort, citation stats)│
│  - ThemeSynthesis (thematic clusters & consensus)      │
│  - ReflectionView (critic gaps & recommended queries)  │
│  - FinalReview (academic literature review document)   │
│  - EvaluationView (intrinsic & benchmark comparison)   │
│  - HistoryDrawer (historical session switching)        │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP REST / SSE Stream
┌───────────────────────────▼────────────────────────────┐
│                    FastAPI API Layer                   │
│  backend/api/routes/research.py                        │
│  backend/api/schemas/research.py                       │
│  backend/api/dependencies.py                           │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                  Application Services                  │
│  backend/services/research_service.py                  │
│  backend/services/research_runner.py                   │
└─────────────┬───────────────────────────┬──────────────┘
              │                           │
              ▼                           ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   Agent Research Engine  │  │    Persistence Layer     │
│   (Member 1 - Frozen)    │  │  backend/database/        │
│   ResearchEngine.run()   │  │  backend/repositories/    │
│   Event Callback Hook    │  │  (Async SQLite / Postgres)│
└──────────────────────────┘  └──────────────────────────┘
```

---

## 2. Core Agent Integration

The application layer invokes Member 1's engine without altering internal heuristics:

```python
engine = ResearchEngine()
result = await engine.run(
    research_question=run.research_question,
    config=ResearchConfig(
        max_iterations=run_config.get("max_iterations", 3),
        target_coverage=run_config.get("target_coverage", 0.85),
        min_new_relevant_papers=run_config.get("min_new_relevant_papers", 1),
        llm_provider=run_config.get("llm_provider", "mock"),
        mock_mode=run_config.get("mock_mode", True),
        temperature=run_config.get("temperature", 0.2),
        event_callback=_event_callback,  # Real-time event telemetry bridge
    )
)
```

### Event Streaming Bridge
During execution, `ResearchEngine` passes each `AgentEvent` to the async callback:
1. The event is saved into the database (`AgentEventModel` via `EventRepository`).
2. Current iteration index and coverage score are updated on the active `ResearchRunModel`.
3. The event is pushed into in-memory subscriber queues for Server-Sent Events (`GET /api/research/{id}/events/stream`).

---

## 3. Database Schema

Managed via SQLAlchemy async ORM (`backend/database/models.py`):

1. **`research_runs`**:
   - `id`: Primary key (UUID string)
   - `research_question`: User inquiry
   - `status`: `'pending'`, `'running'`, `'completed'`, `'failed'`, `'cancelled'`
   - `created_at`, `updated_at`, `started_at`, `completed_at`
   - `current_iteration`, `max_iterations`, `coverage`
   - `stopping_reason`, `error`
   - `config`, `final_review`, `synthesis`, `reflection`, `evaluation`, `metadata_json`

2. **`research_iterations`**:
   - `id`: Primary key
   - `run_id`: Foreign key $\to$ `research_runs.id`
   - `iteration_number`: 1-based index
   - `search_plan`: Decomposed sub-questions, keywords, queries
   - `queries`: Array of executed search strings
   - `retrieved_count`, `new_papers_count`, `relevant_count`, `coverage`
   - `reflection`: Critic assessment JSON

3. **`papers`**:
   - Canonical catalog deduplicated across all runs:
   - `id`, `title`, `authors`, `abstract`, `year`, `venue`, `doi`, `url`, `source`, `citation_count`, `publication_date`, `categories`, `external_ids`

4. **`research_run_papers`**:
   - Relationship link table:
   - `run_id`, `paper_id`, `iteration_number`, `is_relevant`, `relevance_score`, `relevance_reason`

5. **`themes`**:
   - `run_id`, `theme_id`, `title`, `description`, `paper_ids`, `key_findings`, `contradictions_or_tensions`

6. **`agent_events`**:
   - Audit trail of execution steps:
   - `run_id`, `event_type`, `iteration`, `message`, `timestamp`, `payload`

---

## 4. API Endpoints Reference

All routes are mounted under `/api`:

### `POST /api/research`
Initiates an autonomous literature review.
- Request body:
  ```json
  {
    "research_question": "What are current methods for factuality evaluation in retrieval-augmented generation?",
    "config": {
      "max_iterations": 3,
      "target_coverage": 0.85,
      "mock_mode": true
    }
  }
  ```
- Response (201 Created): `ResearchRunResponse`

### `GET /api/research`
Returns list of all historical runs sorted by descending creation time.

### `GET /api/research/{id}`
Returns status and metrics for a specific run.

### `GET /api/research/{id}/iterations`
Returns per-iteration audit records, queries executed, and critic reflection snapshots.

### `GET /api/research/{id}/papers`
Query parameters:
- `is_relevant` (`true` | `false`)
- `source` (`arxiv` | `semantic_scholar` | `crossref`)
- `min_relevance` (float `0.0` - `1.0`)
- `search` (keyword in title, abstract, or authors)
- `sort_by` (`relevance` | `citations` | `year` | `title`)

### `GET /api/research/{id}/themes`
Returns extracted thematic clusters with associated paper IDs and consolidated findings.

### `GET /api/research/{id}/events`
Returns full trace or incremental events after `after_id`.

### `GET /api/research/{id}/events/stream`
Server-Sent Events (SSE) connection streaming `AgentEvent`s in real time as the agent executes.

### `GET /api/research/{id}/result`
Returns the final synthesized literature review document, executive summary, consensus findings, and research gaps.

### `GET /api/research/{id}/evaluation`
Returns coverage, relevance, coherence, citation statistics, and curated ground-truth benchmark comparison (when available).

### `POST /api/research/{id}/cancel`
Cancels an active running loop.

---

## 5. Frontend Features

- **Responsive Design**: Adapts seamlessly to Desktop, Tablet, and Mobile.
- **Academic Aesthetic**: High-contrast typography (Inter + Newsreader serif), minimal cognitive load, professional metadata badges.
- **Real-Time Visibility**: Live checkmarks, spinners, and gap warnings as agent progresses.
- **Paper Explorer**: Sortable, filterable catalog with DOI deep-links and relevance rationales.
- **Markdown Export**: Instant copy-to-clipboard or `.md` file download of the synthesized literature review.
- **Session History**: Persisted in SQLite/PostgreSQL, fully reloadable without losing progress.
