# ResearchLoop AI — Complete Project Audit & Remediation Report

**Audit Date:** 2026-10-24  
**Project Version:** `0.1.0`  
**Overall Readiness Status:** **PASS** (100% of offline/mock acceptance criteria verified; live external API smoke tests opt-in with credentials)

---

## 1. Executive Summary & Discovered Architecture

`researchloop-ai` is an autonomous agentic AI pipeline for conducting scientific literature reviews through iterative planning, multi-source academic retrieval, deduplication, relevance filtering, cross-paper thematic synthesis, critic self-reflection, and targeted replanning.

### Verified Tech Stack
- **Backend Framework:** Python 3.13, FastAPI (`>=0.111.0`), Uvicorn (`>=0.30.0`), Pydantic v2 (`>=2.7.0`), `httpx` (`>=0.27.0`)
- **Database & Persistence:** SQLAlchemy 2.0 Async ORM (`AsyncSession`, `create_async_engine`), `aiosqlite` (`sqlite+aiosqlite:///./researchloop.db` default for zero-credential local operation), PostgreSQL (`postgresql+asyncpg`) compatible
- **Agent Engine (`backend/agent/`):**
  - Orchestrator: `ResearchEngine` (`backend/agent/orchestration/engine.py`)
  - Sub-agents: `PlanningAgent`, `MultiProviderRetriever`, `Deduplicator`, `RelevanceFilter`, `SynthesisAgent`, `CriticAgent`, `ReplanningAgent`
  - Academic Providers: `ArxivProvider` (Atom XML), `SemanticScholarProvider` (Graph API v1), `CrossrefProvider` (REST API), `MockAcademicProvider` (deterministic 8-paper corpus)
  - LLM Providers (`backend/providers/llm/`): `OpenAIProvider`, `AnthropicProvider`, `GeminiProvider`, `MockLLMProvider`
  - Caching: `QueryCache` (`backend/agent/core/cache.py`) with SHA-256 keying across memory and disk (`.cache/researchloop`)
  - Evaluation: Intrinsic metrics (`compute_coverage`, `compute_relevance`, `compute_coherence`, `compute_citation_distribution`) and ground-truth benchmark comparison (`compare_against_benchmark`)
- **Frontend (`frontend/`):** React 18.3, TypeScript 5.6, Vite 6.x, `lucide-react`, Vitest 5.0 + React Testing Library + `jsdom`

---

## 2. Baseline Assessment

- **Git Branch:** `main` (clean working tree at baseline commit `42a7c33`)
- **Backend Baseline Tests:** 46 passed, 2 skipped (opt-in live smoke tests)
- **Frontend Baseline Tests:** 4 test files (8 tests) passed; `tsc && vite build` succeeded

---

## 3. Complete Functionality Inventory

| Component / Route / Feature | Expected Behavior | Actual Implementation | Existing & Added Tests | Defects Found & Fixed | Final Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET /api/health` | Return service status, version, operational mode, and LLM provider | `backend/api/routes/health.py` | `test_health_endpoint` | None | **PASS** |
| `POST /api/research` | Validate inquiry (5–1000 chars), persist run, start background runner | `backend/api/routes/research.py` | `test_validation_errors_create_research`, `test_create_and_get_research` | None | **PASS** |
| `GET /api/research` | List historical runs with pagination (`limit`, `offset`) | `backend/api/routes/research.py` | `test_create_and_get_research` | None | **PASS** |
| `GET /api/research/{id}` | Return run status, iteration counts, coverage, paper/theme counts | `backend/api/routes/research.py` | `test_create_and_get_research`, `test_unknown_run_returns_404` | None | **PASS** |
| `GET /api/research/{id}/iterations` | Return per-iteration plans, executed queries, counts, reflections | `backend/api/routes/research.py` | `test_full_end_to_end_research_lifecycle` | Fixed mid-transaction commit in `_persist_result` | **PASS** |
| `GET /api/research/{id}/papers` | Filter by `is_relevant`, `source`, `min_relevance`, `search` (title, abstract, authors), and sort | `backend/api/routes/research.py`, `paper_repository.py` | `test_papers_filtering_and_author_search` | Added author search filter (`cast(PaperModel.authors, String).ilike`) to match documented contract | **PASS** |
| `GET /api/research/{id}/themes` | Return synthesized thematic clusters and supporting paper IDs | `backend/api/routes/research.py` | `test_full_end_to_end_research_lifecycle` | None | **PASS** |
| `GET /api/research/{id}/events` | Return chronological `AgentEvent` telemetry trace (`after_id` cursor) | `backend/api/routes/research.py` | `test_full_end_to_end_research_lifecycle` | None | **PASS** |
| `GET /api/research/{id}/events/stream` | Stream real-time `AgentEvent`s via Server-Sent Events (SSE) | `backend/api/routes/research.py` | `test_sse_stream_completed_run`, `test_unknown_run_returns_404` | Fixed failure event broadcast when engine returns `status="failed"` | **PASS** |
| `GET /api/research/{id}/result` | Return synthesized literature review, themes, consensus, and gaps | `backend/api/routes/research.py` | `test_full_end_to_end_research_lifecycle` | None | **PASS** |
| `GET /api/research/{id}/evaluation` | Return intrinsic & ground-truth benchmark recall/overlap metrics | `backend/api/routes/research.py` | `test_full_end_to_end_research_lifecycle` | None | **PASS** |
| `POST /api/research/{id}/cancel` | Cancel active background asyncio task and mark run `cancelled` | `backend/api/routes/research.py` | `test_cancel_research_endpoint` | None | **PASS** |
| SPA Static Hosting (`/{full_path:path}`) | Serve `frontend/dist` assets and `index.html` fallback for SPA routes | `backend/api/main.py` | `test_unknown_api_route_returns_404_not_500` | Fixed `/api/*` fallthrough returning `200 null` instead of `404`; added path-traversal guard | **PASS** |
| `ResearchEngine.run()` | Frozen contract executing Planner $\to$ Retriever $\to$ Dedup $\to$ Filter $\to$ Synthesizer $\to$ Critic $\to$ Replanner | `backend/agent/orchestration/engine.py` | `test_orchestrator_multi_iteration_run`, `test_orchestrator_stops_at_max_iterations`, `test_orchestrator_diminishing_returns_stop` | None | **PASS** |
| `PlanningAgent` | Decompose research question into sub-questions, keywords, queries | `backend/agent/planner/planner.py` | `test_planner_normal_question`, `test_planner_fallback_on_llm_failure` | None | **PASS** |
| `MultiProviderRetriever` & Academic Providers | Concurrent query execution across arXiv, Semantic Scholar, Crossref, Mock with retry & failure isolation | `backend/agent/retrieval/` | `test_academic_providers.py` (8 tests including HTTP 429 retry) | None | **PASS** |
| `Deduplicator` | Multi-tier deduplication (DOI, normalized title, cautious fuzzy match with year/author verification) | `backend/agent/filtering/deduplication.py` | `test_deduplication.py` (5 tests) | None | **PASS** |
| `RelevanceFilter` | Score candidate papers concurrently with prompt-injection guards and fallback | `backend/agent/filtering/relevance.py` | `test_relevance.py`, `test_prompt_injection_tag_escape_defense` | Sanitized untrusted fields against `</untrusted_academic_content>` tag breakout | **PASS** |
| `SynthesisAgent` | Extract per-paper analyses, dynamic thematic clusters, consensus, contradictions | `backend/agent/synthesis/synthesizer.py` | `test_synthesizer.py`, `test_prompt_injection_tag_escape_defense` | Sanitized untrusted fields against XML tag breakout | **PASS** |
| `CriticAgent` & `ReplanningAgent` | Evaluate coverage, detect missing topics, generate non-duplicate follow-up queries | `critic.py`, `replanner.py` | `test_critic.py`, `test_replanner.py` | None | **PASS** |
| Frontend UI (`App.tsx` & 11 Components) | Inquiry submission, live SSE + polling progress, timeline, paper explorer, themes, critic, review markdown export, evaluation, history drawer | `frontend/src/` | 5 test suites (15 tests) + production build | Fixed `pending` status polling deadlock, stale state on run switch, error array formatting, URL scheme validation, and form accessibility labels | **PASS** |

---

## 4. Issues Discovered, Root Causes, and Remediation

### P1 — High Severity Issues (Fixed)

1. **ISSUE-01 (P1): Live LLM Provider Configuration Ignored in `ResearchRunner`**
   - **Location:** `backend/services/research_runner.py` (Line 187)
   - **Root Cause:** `llm_provider=run_config.get("llm_provider", "mock" if is_mock else "mock")` hardcoded `"mock"` as the fallback in both branches, ignoring `settings.llm_provider` when a live run was requested without an explicit `llm_provider` field in the request JSON. Additionally, `settings.llm_model` was not used as a fallback.
   - **Fix:** Updated to `"mock" if is_mock else run_config.get("llm_provider", settings.llm_provider)` and `run_config.get("llm_model", settings.llm_model)`.
   - **Verification:** `tests/services/test_research_service.py`.

2. **ISSUE-02 (P1): Unhandled Engine `status="failed"` Return in `ResearchRunner`**
   - **Location:** `backend/services/research_runner.py` (Lines 197–215, 320–330)
   - **Root Cause:** `ResearchEngine.run()` catches fatal exceptions internally and returns a `ResearchResult(status="failed", stop_reason="error: ...")` rather than raising. `ResearchRunner.execute()` unconditionally logged completion, broadcast `research.completed`, and left `ResearchRunModel.error` as `None`.
   - **Fix:** Checked `result.status == "completed"`; broadcast `research.failed` when `result.status == "failed"` and populated `ResearchRunModel.error` in `save_final_result`.
   - **Verification:** Added regression test `test_research_runner_handles_engine_failure` in `tests/services/test_research_service.py`.

3. **ISSUE-03 (P1): Unknown `/api/*` Routes Returned `200 OK` with `null` Body When Frontend Built**
   - **Location:** `backend/api/main.py` (Lines 63–66)
   - **Root Cause:** Catch-all SPA route `@app.get("/{full_path:path}")` checked `if full_path.startswith("api"): return None`, causing FastAPI to serialize `None` as HTTP `200 OK` (`null`) instead of HTTP `404 Not Found`. Also hardened `target_file.resolve().is_relative_to(frontend_dist.resolve())`.
   - **Fix:** Raised `HTTPException(status_code=404, detail="Not Found")` for unmounted `api` paths and non-relative paths.
   - **Verification:** Added regression test `test_unknown_api_route_returns_404_not_500` in `tests/api/test_api.py` and verified against live Uvicorn server.

4. **ISSUE-04 (P1): Frontend Polling/SSE Deadlock When Initial Run Status Is `pending`**
   - **Location:** `frontend/src/App.tsx` (Line 130)
   - **Root Cause:** `POST /api/research` creates the run with `status="pending"` and dispatches the background task. If the HTTP response returned before the background task flipped status to `"running"`, `App.tsx`'s `useEffect` (`activeRun.status !== 'running'`) exited immediately and never polled or opened SSE.
   - **Fix:** Updated `App.tsx` to poll and subscribe when `activeRun.status === 'running' || activeRun.status === 'pending'`, and handle `failed` / `cancelled` events cleanly.

### P2 — Medium Severity Issues (Fixed)

5. **ISSUE-05 (P2): Partial Transaction Commits During `_persist_result` in `ResearchRunner`**
   - **Location:** `backend/services/research_runner.py` (Line 280)
   - **Root Cause:** `_persist_result` flushed papers and links via `session.flush()`, then called `iteration_repo.create(it_model)` which executed `session.commit()` mid-loop before themes and final run status were written. Under concurrent SQLite access or mid-persistence failure, this caused partial state visibility.
   - **Fix:** Added `session.add(it_model)` + `await session.flush()` inside `_persist_result` so all papers, paper links, iterations, themes, and final run state commit atomically in a single transaction at `save_final_result`.
   - **Verification:** `tests/api/test_integration_e2e.py` and `tests/services/test_research_service.py`.

6. **ISSUE-06 (P2): Prompt-Injection XML Tag Escape in Untrusted Paper Metadata**
   - **Location:** `backend/agent/prompts/relevance.py`, `backend/agent/prompts/synthesis.py`
   - **Root Cause:** Untrusted paper titles, authors, and abstracts were interpolated into `<untrusted_academic_content>` blocks without sanitizing closing `</untrusted_academic_content>` tags.
   - **Fix:** Added `_sanitize_untrusted()` helper escaping any closing `</untrusted_academic_content>` tags before prompt construction.
   - **Verification:** Added regression test `test_prompt_injection_tag_escape_defense` in `tests/providers/test_academic_providers.py`.

7. **ISSUE-07 (P2): Missing Author Search in `PaperRepository.get_papers_for_run`**
   - **Location:** `backend/repositories/paper_repository.py` (Lines 125–132)
   - **Root Cause:** `docs/APPLICATION_LAYER_GUIDE.md` documented that `search` filters by keyword in title, abstract, or authors, but `PaperRepository` only searched `title` and `abstract`.
   - **Fix:** Added `cast(PaperModel.authors, String).ilike(search_term)` to the `or_()` clause.
   - **Verification:** Added `test_papers_filtering_and_author_search` in `tests/api/test_api.py`.

8. **ISSUE-08 (P2): Frontend State Stale Data on Run Switching & External Link Scheme Guard**
   - **Location:** `frontend/src/App.tsx`, `frontend/src/components/PaperExplorer.tsx`, `frontend/src/components/FinalReview.tsx`, `frontend/src/services/api.ts`
   - **Root Cause:** Switching to an incomplete or failed run in `HistoryDrawer` left the previous run's `result` and `evaluation` state displayed; Pydantic 422 array errors rendered as `[object Object]`; external `paper.url` links did not validate `http://` or `https://` protocol.
   - **Fix:** Cleared `result` and `evaluation` when switching runs, formatted Pydantic error arrays into readable strings, and added `isSafeUrl()` protocol checks.

### P3 — Low Severity Issues (Fixed)

9. **ISSUE-09 (P3): Configuration & Accessibility Improvements**
   - **Location:** `.env.example`, `pyproject.toml`, `README.md`, `frontend/src/components/ResearchForm.tsx`, `PaperExplorer.tsx`, `HistoryDrawer.tsx`
   - **Fix:** Aligned `.env.example` default `DATABASE_URL` with local SQLite (`sqlite+aiosqlite:///./researchloop.db`) so `cp .env.example .env` works out-of-the-box without requiring a PostgreSQL server; included full-stack dependencies in `pyproject.toml`; added `aria-label` and `htmlFor`/`id` attributes to form inputs and controls.
