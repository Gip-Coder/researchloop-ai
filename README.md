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
Multi-Agent Loop: Planning → Retrieval → Deduplication → Relevance Filtering → Thematic Synthesis → Critic Reflection → Replanning
       ↓
Persistence Layer (SQLAlchemy ORM + SQLite/PostgreSQL)
       ↓
Frontend Visualization (Dashboard, Trace, Papers, Themes, Gaps, Review, Evaluation, History)
```

---

## Research Quality & Selection Policies

ResearchLoop AI implements rigorous academic selection and evidence synthesis standards:

### 1. Publication-Year Boundary & Foundational Exceptions
- **Default Minimum Year**: `2019` (`MIN_PUBLICATION_YEAR=2019`).
- **Policy**: Only papers published in 2019 or later are accepted for substantive thematic synthesis and bibliography by default.
- **Foundational Exceptions**: Pre-2019 seminal papers are strictly excluded by default unless `ALLOW_FOUNDATIONAL_EXCEPTIONS=true` is explicitly enabled. When enabled, exceptions are clearly flagged with `[Foundational Exception]` tags in the UI and bibliography.
- **Deterministic Date Handling**: Authoritative date records from arXiv and Crossref are parsed into four-digit years. Missing or malformed dates are handled deterministically without fabricating dates.

### 2. Citation-Count Preference (10–15 Citations)
- **Configurable Range**: Preferred 10–15 citations (`PREFERRED_MIN_CITATIONS=10`, `PREFERRED_MAX_CITATIONS=15`).
- **Preference-Based Ranking**: Citation counts serve as a ranking preference rather than a hard exclusion filter. Papers with citations in the 10–15 range are prioritized; high-relevance papers (relevance score $\ge 0.85$) outside the range remain eligible to ensure cutting-edge findings are not omitted.
- **Unknown Citations Handling**: arXiv and non-indexed records do not fabricate zero citations; missing counts are preserved as `None`/`Unavailable` (`citation_count_available=False`) and ranked fairly in an unknown-citation tier. Strict filtering (`STRICT_CITATION_FILTERING=true`) can be toggled if required.

### 3. Phrase-Based Academic Search & Provenance
- **Multiword Phrase Queries**: The planner and replanner generate meaningful multiword quoted phrases (e.g., `"retrieval-augmented generation" evaluation benchmark`) preserving quotes across arXiv and Crossref search APIs.
- **Query Diversity & Provenance**: Search plans span core concepts, evaluation methodology, empirical findings, and identified gaps. Every discovered paper records its `matched_queries` for auditability.

### 4. Evidence Pool Sizing (6–10 Papers)
- **Target**: Synthesize 6–10 unique, relevant papers per completed review whenever sufficient evidence exists (`MIN_SYNTHESIS_PAPERS=6`, `TARGET_SYNTHESIS_PAPERS=8`, `MAX_SYNTHESIS_PAPERS=10`).
- **Insufficient Evidence Warnings**: If fewer than 6 papers meet relevance criteria, the system flags an `insufficient_evidence_warning` in the final review and UI rather than lowering quality thresholds or inventing citations.

---

## Retrieval Source Configuration & Performance

ResearchLoop AI defaults to `PREFERRED_SOURCES=arxiv,crossref`.

### Why Semantic Scholar is Excluded by Default
- **Severe Rate Limiting (HTTP 429)**: The public unauthenticated Semantic Scholar API aggressively throttles requests, causing multi-second sleep retries and request timeouts.
- **Latency Optimization**: By default querying arXiv and Crossref concurrently, median search latency is reduced significantly, eliminating repeated backoff stalls while retaining broad academic coverage.
- **Optional Enablement**: To re-enable Semantic Scholar with an API key, set in `.env`:
  ```ini
  PREFERRED_SOURCES=arxiv,crossref,semantic_scholar
  SEMANTIC_SCHOLAR_API_KEY=your-api-key-here
  ```

---

## Research History Deletion & Authoritative Timestamps

### History Deletion Endpoints
- `DELETE /api/research/{run_id}`: Deletes a specific research run and cascades cleanup across child records (iterations, themes, events, and paper run links). Returns HTTP 404 for nonexistent run IDs.
- `DELETE /api/research`: Clears all recorded research runs and associated data.
- **Frontend History Drawer**: Features safe two-click inline confirmation for deleting individual runs and clearing all history, preventing accidental data loss.

### Authoritative UTC Timestamps
- All API timestamps (`created_at`, `updated_at`, `started_at`, `completed_at`, and event `timestamp`) are serialized in ISO 8601 format with explicit UTC offsets (`YYYY-MM-DDTHH:MM:SSZ`).
- The frontend renders timestamps in the user's local timezone and never regenerates timestamps on re-render.

---

## Frontend Smoothness & Live Execution Feed

- **Container-Scoped Scrolling**: Auto-scrolling during research execution is strictly scoped to the event feed container (`containerRef.current`), completely preventing jarring full-page viewport jumps.
- **Follow Latest Mode**: Automatically follows new incoming events. If the user scrolls up to inspect previous logs, auto-follow smoothly pauses and reveals a floating "Follow latest" button to resume following on click.
- **Visual Stage Progression**: Displays active research stages (`Planning` $\to$ `Retrieval` $\to$ `Thematic Synthesis` $\to$ `Critic Evaluation` $\to$ `Replanning / Finalizing`) with real-time status spinners and completion checks.
- **Accessibility**: Automatically adheres to `prefers-reduced-motion` settings for users requesting reduced motion.

---

## Environment Variables Reference

| Variable | Default | Description |
| :--- | :--- | :--- |
| `RESEARCHLOOP_MODE` | `mock` | `'mock'` (offline deterministic fixtures) or `'live'` (real APIs) |
| `LLM_PROVIDER` | `mock` | `'mock'`, `'openai'`, `'anthropic'`, `'gemini'`, or `'ollama'` |
| `LLM_MODEL` | *(provider default)* | Model override (e.g. `gpt-4o-mini`, `gemini-1.5-flash`, `llama3.2:3b`) |
| `PREFERRED_SOURCES` | `arxiv,crossref` | Comma-separated retrieval providers (`arxiv,crossref,semantic_scholar`) |
| `MIN_PUBLICATION_YEAR` | `2019` | Default minimum publication year for academic papers |
| `PREFERRED_MIN_CITATIONS` | `10` | Preferred minimum citations for ranking |
| `PREFERRED_MAX_CITATIONS` | `15` | Preferred maximum citations for ranking |
| `STRICT_CITATION_FILTERING` | `false` | Whether to strictly exclude papers outside citation range |
| `MIN_SYNTHESIS_PAPERS` | `6` | Minimum desired papers in final synthesis evidence pool |
| `TARGET_SYNTHESIS_PAPERS` | `8` | Target number of papers for thematic synthesis |
| `MAX_SYNTHESIS_PAPERS` | `10` | Maximum papers to include in synthesis |
| `ALLOW_FOUNDATIONAL_EXCEPTIONS` | `false` | Allow seminal pre-2019 papers with explicit badge |
| `CROSSREF_MAILTO` | `researcher@example.com` | Polite pool contact email for Crossref API |
| `DATABASE_URL` | `sqlite+aiosqlite:///./researchloop.db` | Async SQLAlchemy database URL |

---

## Primary API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/research` | Create & launch autonomous research loop in background |
| `GET` | `/api/research` | List historical research runs (sorted by `created_at` desc) |
| `DELETE` | `/api/research` | Delete all historical research runs and cascade child records |
| `GET` | `/api/research/{id}` | Get status, coverage, and overview of a run |
| `DELETE` | `/api/research/{id}` | Delete a specific research run and cascade its child records |
| `GET` | `/api/research/{id}/iterations` | Get iterative loop audit logs & plans |
| `GET` | `/api/research/{id}/papers` | Query discovered papers with filters (`is_relevant`, `source`, `sort_by`, `search`) |
| `GET` | `/api/research/{id}/themes` | Get extracted thematic clusters |
| `GET` | `/api/research/{id}/events` | Get agent event trace and execution logs |
| `GET` | `/api/research/{id}/events/stream` | Server-Sent Events (SSE) live real-time stream |
| `GET` | `/api/research/{id}/result` | Get synthesized literature review & report |
| `GET` | `/api/research/{id}/evaluation` | Get intrinsic & benchmark evaluation metrics |
| `POST` | `/api/research/{id}/cancel` | Cancel an active research loop |
| `GET` | `/api/health` | Service health and operating mode |

Interactive Swagger documentation is available at `http://127.0.0.1:8000/docs`.

---

## Testing & Verification

All tests run **100% offline with zero external API credentials** by default.

### 1. Backend Tests (Pytest)
```powershell
uv run --extra test pytest
```
Runs 91+ unit, integration, and API tests covering:
- Publication-year filtering, missing dates, and foundational exceptions
- Citation range ranking (10–15 preference), strict mode, and unavailable citation handling
- Phrase-based search queries and deduplication
- Evidence pool sizing and insufficient evidence warnings
- Retrieval source configuration and Semantic Scholar exclusion
- Individual run deletion (`DELETE /api/research/{id}`) with cascade verification
- Clear-all runs (`DELETE /api/research`)
- Authoritative UTC ISO 8601 timestamp formatting

### 2. Frontend Tests & Build (Vitest & TypeScript)
```powershell
cd frontend
npm test
npm run build
```
Runs 25 Vitest tests verifying:
- `HistoryDrawer`: inline two-click deletion confirmation, clear-all confirmation, and timestamp formatting
- `LiveProgress`: container-scoped scrolling, auto-follow pause/resume pill, and research stage indicators
- `PaperExplorer`: unavailable citation fallback, preferred citation range highlight, foundational exception tag, and matched queries
- `FinalReview`: evidence pool badge, target indicators, and insufficient evidence warnings
- Production build compilation and TypeScript verification

---

## Single-User SQLite Boundary

ResearchLoop AI defaults to a local SQLite database (`researchloop.db`). Under SQLite:
- Research history deletion uses cascading deletes on foreign keys (`ON DELETE CASCADE` via SQLAlchemy ORM).
- Deletion operations execute within explicit transaction boundaries (`session.commit()`).
- In multi-process production deployments, configure `DATABASE_URL` to point to a PostgreSQL instance (`postgresql+asyncpg://user:pass@host/dbname`).
