# ResearchLoop AI — Known Issues, Limitations & External Dependencies

**Last Updated:** 2026-10-24

All reproducible P0, P1, P2, and P3 defects discovered during the project audit have been resolved and verified with automated regression tests. This document records remaining architectural boundaries, optional external dependencies, and environment-specific considerations.

---

## 1. External API Credentials (Blocked for Unauthenticated Live LLM Execution)

- **Description:** Running the pipeline in **Live Mode** (`RESEARCHLOOP_MODE=live`) with `LLM_PROVIDER` set to `openai`, `anthropic`, or `gemini` requires a valid API key (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GEMINI_API_KEY`) configured in `.env`.
- **Default Behavior:** Out-of-the-box (`RESEARCHLOOP_MODE=mock`), the system runs 100% offline with zero credentials required using deterministic fixtures (`MockLLMProvider` and `MockAcademicProvider`).
- **Verification Step When Credentials Are Provided:**
  ```powershell
  $env:RUN_LIVE_API_TESTS="1"
  python -m pytest tests/providers/test_live_smoke.py -v
  ```

---

## 2. Single-Process In-Memory Task & SSE State

- **Description:** `ResearchRunner` manages active background `asyncio.Task` handles (`_running_tasks`) and Server-Sent Events (SSE) subscriber queues (`_subscribers`) in process memory (`backend/services/research_runner.py`).
- **Impact:** When running Uvicorn with multiple worker processes (`--workers > 1`), SSE connections or cancellation requests routed to a different worker than the one executing the background task will not see the in-memory queue/task, although all events and state updates are persisted to the database and remain visible via HTTP polling (`GET /api/research/{id}/events`).
- **Recommended Action:** Run Uvicorn with a single async worker (`python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000`) or use Redis Pub/Sub if scaling horizontally across multiple processes.

---

## 3. Database Schema Initialization vs. Alembic Migrations

- **Description:** On startup (`lifespan` in `backend/api/main.py`), `init_db()` automatically creates all database tables via `Base.metadata.create_all` (`backend/database/session.py`). While `alembic` is included in `requirements.txt` for future schema evolution, an `alembic/` migration directory is not currently used because `init_db()` handles clean schema creation automatically for both SQLite and PostgreSQL.
- **Recommended Action:** If modifying existing column types in an established production PostgreSQL database, initialize Alembic (`alembic init alembic`) to generate incremental DDL migrations.
