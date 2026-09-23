# researchloop-ai

**An agentic AI pipeline for autonomous literature review with iterative planning, retrieval, synthesis, and self-reflection.**

---

## Architecture Overview

```text
Research Question
       ↓
Planning Agent (sub-questions, queries, inclusion/exclusion criteria)
       ↓
Academic Retrieval (arXiv, Semantic Scholar, Crossref with failure isolation)
       ↓
Deduplication (DOI, normalized title, cautious fuzzy matching)
       ↓
Relevance Filtering (evaluation against criteria with reasoning)
       ↓
Synthesis Agent (per-paper analysis & dynamic cross-paper thematic clustering)
       ↓
Critic / Self-Reflection (coverage, relevance, recency, gap detection)
       ↓
Replanning Agent (gap-targeted queries)
       ↓
Next Iteration / Stopping Conditions
       ↓
Canonical ResearchResult & Agent Event Stream
```

---

## Member 1 Deliverables (AI / Agent Engine)

- **Strict Isolation**: Exclusively implemented under `backend/agent/`, `backend/providers/`, `tests/`, and `docs/`. Member 2's components (`backend/api/`, `backend/database/`, `frontend/`) remain completely untouched.
- **Frozen Contract**: Full public API contract defined in [`docs/AGENT_ENGINE_CONTRACT.md`](docs/AGENT_ENGINE_CONTRACT.md).
- **Mock Mode**: Fully offline, zero-credential execution with deterministic realistic fixtures.
- **Evaluation Suite**: Includes `compute_coverage()`, `compute_relevance()`, `compute_coherence()`, `compute_paper_recall()`, `compute_topic_coverage()`, and ground-truth benchmark comparison.

---

## Getting Started

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Run Automated Tests
All automated tests are 100% mocked by default:
```powershell
pytest tests/ -v
```

### 3. Run Local CLI
Test the autonomous research loop in mock mode:
```powershell
python -m backend.agent.cli "How does retrieval augmented generation improve factuality in large language models?" --mock
```

To run with live LLM & academic providers (requires API keys in `.env`):
```powershell
python -m backend.agent.cli "Your research question" --live --provider openai
```

---

## Integration Guide for Member 2

Refer directly to [`docs/AGENT_ENGINE_CONTRACT.md`](docs/AGENT_ENGINE_CONTRACT.md) for public interfaces, Pydantic schemas, event streaming details, and error handling specifications.
