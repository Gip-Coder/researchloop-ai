# ResearchLoop AI — Application Security Audit Report

**Audit Date:** 2026-10-24  
**Scope:** Backend API (`backend/api/`), Agent Engine & Prompts (`backend/agent/`), LLM & Academic Providers (`backend/providers/`), Persistence (`backend/database/`, `backend/repositories/`), Frontend (`frontend/src/`), and Configuration.

---

## 1. Threat Areas Inspected

| Threat Category | Inspection Method | Status | Findings Summary |
| :--- | :--- | :---: | :--- |
| **Secrets & Credentials Exposure** | Inspected `.env.example`, `.gitignore`, git history, and frontend bundle (`frontend/dist/`) | **PASS** | `.env` is gitignored; no real API keys or tokens exist in repo or built JS assets. |
| **SQL Injection (SQLi)** | Audited all SQLAlchemy queries across `backend/repositories/*.py` | **PASS** | All database queries use SQLAlchemy 2.0 parameterized ORM constructs (`select()`, `.where()`, `.ilike()`). Zero raw SQL string concatenation. |
| **Prompt Injection via Untrusted Literature** | Audited `backend/agent/prompts/relevance.py` and `synthesis.py` | **FIXED** | Added `_sanitize_untrusted()` to prevent malicious paper titles/abstracts from breaking out of `<untrusted_academic_content>` XML boundaries, combined with strict Pydantic output schema validation. |
| **Cross-Site Scripting (XSS) & Unsafe URLs** | Audited all React components (`frontend/src/components/*.tsx`) | **FIXED** | Zero use of `dangerouslySetInnerHTML`. Added `isSafeUrl()` protocol validation (`http://` or `https://`) on external `paper.url` links in `PaperExplorer.tsx` and `FinalReview.tsx`. |
| **Path Traversal in Static File Serving** | Audited `serve_spa` in `backend/api/main.py` | **FIXED** | Enforced `target_file.resolve().is_relative_to(frontend_dist.resolve())` and proper `HTTPException(404)` on unmounted `/api/*` paths. |
| **CORS Policy Configuration** | Audited `CORSMiddleware` in `backend/api/main.py` | **FIXED** | Restricted default origins to local dev ports (`3000`, `5173`) and disabled `allow_credentials` if wildcard `*` is configured in `ALLOWED_ORIGINS`. |
| **Input Validation & DoS Bounds** | Audited `backend/api/schemas/research.py` and route query parameters | **PASS** | `research_question` bounded (`min_length=5, max_length=1000`), `max_iterations` bounded (`ge=1, le=10`), pagination `limit` bounded (`le=100` on runs, `le=1000` on events). |
| **Unbounded Loops & External Request Timeouts** | Audited `ResearchEngine`, `AcademicSource`, and `LLMProvider` | **PASS** | `ResearchEngine` enforces `max_iterations`, `target_coverage`, and `min_new_relevant_papers`. `httpx.AsyncClient` enforces explicit timeouts (`15.0s` academic, `60.0s` LLM) and bounded retries (`max_retries=3`). |

---

## 2. Confirmed Vulnerabilities & Remediations Applied

### SEC-01 (Medium): XML Boundary Escape in Untrusted Academic Content Prompts
- **Description:** Retrieved paper titles, author names, and abstracts from external academic APIs are untrusted inputs. Previously, they were interpolated directly into `<untrusted_academic_content>` blocks in `build_relevance_prompt` and `build_synthesis_prompt`. A paper abstract containing `</untrusted_academic_content>` could close the tag early and inject instructions into the surrounding prompt context.
- **Remediation:** Implemented `_sanitize_untrusted()` in `backend/agent/prompts/relevance.py` and `backend/agent/prompts/synthesis.py` to neutralize closing `</untrusted_academic_content>` tags before prompt assembly, alongside strict `LLMProvider.generate_structured()` Pydantic schema validation.
- **Regression Test:** `tests/providers/test_academic_providers.py::test_prompt_injection_tag_escape_defense`.

### SEC-02 (Low): Unvalidated URL Scheme in External Paper Links
- **Description:** `PaperExplorer.tsx` and `FinalReview.tsx` rendered `<a href={paper.url}>` directly from paper metadata. While academic providers normally return `http://` or `https://` URLs, untrusted metadata could theoretically supply a `javascript:` URI.
- **Remediation:** Added `isSafeUrl()` guard verifying `url.startsWith('http://') || url.startsWith('https://')` before rendering `<a href={paper.url}>`.

### SEC-03 (Low): SPA Catch-All Path Resolution & Wildcard CORS Credentials
- **Description:** In `backend/api/main.py`, `serve_spa` resolved `frontend_dist / full_path` without verifying containment inside `frontend_dist.resolve()`, and returned `None` (`200 OK` null body) for unknown `/api/*` paths. Additionally, `allow_credentials=True` was paired with `allow_origins=["*"]` when `ALLOWED_ORIGINS=*`.
- **Remediation:** Added `.resolve().is_relative_to(frontend_dist.resolve())`, raised `HTTPException(status_code=404)` for unknown `/api` routes, and set `allow_credentials=not is_wildcard`.

---

## 3. Remaining Security Considerations & Architectural Limitations

1. **Authentication & Authorization:** By design for the current single-tenant / local academic workbench specification, the API does not enforce user authentication or per-user RBAC. If deployed to a public multi-tenant environment, OAuth2/JWT authentication middleware and rate-limiting (e.g., `slowapi` or reverse-proxy rate limits) should be placed in front of `/api/research`.
2. **In-Memory Background Task & SSE Registry:** Active tasks (`_running_tasks`) and SSE queues (`_subscribers`) are held in process memory, which is appropriate for single-worker deployments. Multi-worker horizontal scaling would require Redis pub/sub and a distributed task queue.
