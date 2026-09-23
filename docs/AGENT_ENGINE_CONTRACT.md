# Agent Engine Integration Contract (Member 1 $\to$ Member 2)

**Project:** `researchloop-ai`  
**Author:** Member 1 (AI / Agent Engine)  
**Target Consumer:** Member 2 (API, Database, Background Workers & Frontend)  
**Contract Version:** `1.0.0` (Frozen)  
**Branch:** `member1/agent-engine`

---

## 1. Executive Summary

Member 2 consumes the **AI / Agent / Research Engine** as a black box. Member 2 does not need to understand or modify the internal heuristics of the Planner, Multi-provider Retriever, Deduplicator, Relevance Filter, Synthesizer, Critic, or Replanner.

Member 2 interacts exclusively through:
1. The primary entry point class: `backend.agent.ResearchEngine`
2. Shared Pydantic data schemas: `ResearchConfig`, `ResearchResult`, and `AgentEvent`
3. Zero-dependency Mock Mode (`RESEARCHLOOP_MODE=mock`) for offline API/UI development and integration testing.

---

## 2. Public Interface

Member 2 imports the engine and configuration models directly from `backend.agent`:

```python
from backend.agent import ResearchEngine, ResearchConfig, ResearchResult, AgentEvent
```

### Method Signature

```python
class ResearchEngine:
    def __init__(self, default_config: ResearchConfig | None = None):
        ...

    async def run(
        self,
        research_question: str,
        config: ResearchConfig | None = None
    ) -> ResearchResult:
        """
        Executes the autonomous literature review loop.

        Args:
            research_question: The user-supplied research inquiry.
            config: Optional runtime configuration override.

        Returns:
            ResearchResult: Canonical result object containing papers, themes,
                            synthesis, iterations, and event traces.
        """
```

---

## 3. Input Contract (`ResearchConfig`)

Schema defined in `backend.agent.models.research.ResearchConfig`:

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `max_iterations` | `int` | `3` | Maximum iterative loops before stopping. |
| `target_coverage` | `float` | `0.85` | Coverage score threshold (0.0 to 1.0) to declare completion. |
| `min_new_relevant_papers` | `int` | `1` | Minimum new relevant papers in an iteration to avoid diminishing returns stop. |
| `llm_provider` | `str` | `"mock"` | Active LLM: `"mock"`, `"openai"`, `"anthropic"`, `"gemini"`. |
| `llm_model` | `str \| None` | `None` | Optional model name override (e.g. `"gpt-4o-mini"`, `"claude-3-5-sonnet-20241022"`). |
| `preferred_sources` | `list[str]` | `["arxiv", "semantic_scholar", "crossref"]` | Academic sources to retrieve from. |
| `mock_mode` | `bool` | `False` | When `True`, forces offline execution using deterministic fixtures. |
| `temperature` | `float` | `0.2` | Sampling temperature for LLM agents. |
| `academic_request_timeout` | `float` | `15.0` | Timeout per academic provider request in seconds. |
| `academic_max_retries` | `int` | `3` | Max exponential backoff retries on academic provider rate limits or timeouts. |
| `cache_enabled` | `bool` | `True` | Enables SHA-256 disk and in-memory caching of search queries. |
| `event_callback` | `Callable \| None` | `None` | Optional `async` or `sync` callable receiving `AgentEvent` objects in real time. |

---

## 4. Output Contract (`ResearchResult`)

Schema defined in `backend.agent.models.research.ResearchResult`:

```json
{
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "completed",
  "research_question": "How does retrieval augmented generation improve factuality in large language models?",
  "iterations": [
    {
      "iteration": 1,
      "search_plan": {
        "research_question": "...",
        "sub_questions": ["..."],
        "keywords": ["..."],
        "search_queries": ["..."],
        "preferred_sources": ["arxiv", "semantic_scholar", "crossref"],
        "date_range": { "start_year": 2020, "end_year": 2026 },
        "inclusion_criteria": ["..."],
        "exclusion_criteria": ["..."]
      },
      "queries_executed": ["..."],
      "papers_retrieved_count": 42,
      "new_papers_count": 8,
      "relevant_papers_count": 7,
      "coverage_score": 0.65,
      "reflection": {
        "coverage_score": 0.65,
        "relevance_score": 0.88,
        "missing_topics": ["Standardized quantitative evaluation benchmarks (RGB, FactScore)"],
        "weak_areas": ["Empirical comparison across dense vs hybrid architectures"],
        "contradictions": [],
        "outdated_areas": [],
        "recommended_queries": ["retrieval augmented generation hallucination evaluation benchmark"],
        "should_replan": true,
        "reason": "Foundational concepts covered, but benchmark evaluations remain under-represented.",
        "evaluation_type": "llm_critic"
      },
      "timestamp": "2026-09-23T18:00:00Z"
    }
  ],
  "papers": [
    {
      "id": "mock-lewis-2020-rag",
      "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
      "authors": ["Patrick Lewis", "Ethan Perez"],
      "abstract": "Large pre-trained language models store factual knowledge in their parameters...",
      "year": 2020,
      "venue": "NeurIPS",
      "doi": "10.5555/3495724.3496517",
      "url": "https://arxiv.org/abs/2005.11401",
      "source": "arxiv",
      "citation_count": 4820,
      "publication_date": "2020-05-22",
      "external_ids": { "arxiv": "2005.11401" },
      "categories": ["cs.CL", "cs.AI"],
      "raw_source_id": "2005.11401",
      "is_relevant": true,
      "relevance_score": 0.89,
      "relevance_reason": "Directly addresses retrieval-augmented architectures and factual consistency."
    }
  ],
  "relevant_papers": [ /* Subset of papers where is_relevant == true */ ],
  "themes": [
    {
      "id": "theme-1",
      "title": "Grounding Generative Outputs in Non-Parametric Memory",
      "description": "Core architectural research focusing on coupling pre-trained models with external vector indices.",
      "paper_ids": ["mock-lewis-2020-rag", "mock-karpukhin-2020-dpr"],
      "key_findings": [
        "Non-parametric grounding significantly lowers hallucinations on knowledge-intensive QA."
      ],
      "contradictions_or_tensions": []
    }
  ],
  "synthesis": {
    "paper_analyses": [
      {
        "paper_id": "mock-lewis-2020-rag",
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "research_problem": "Mitigating hallucinations and factual drift in LLM text generation.",
        "methodology": "Dual-encoder dense retrieval integrated with cross-attention generative decoder.",
        "dataset": "NaturalQuestions, HotpotQA, and FactScore benchmarks.",
        "key_findings": ["External retrieval reduces factual errors by 32%."],
        "contribution": "End-to-end framework coupling parametric and non-parametric memory.",
        "limitations": ["Susceptible to distraction when documents contain conflicting claims."],
        "relevance": "Directly demonstrates mechanism of factual grounding via external retrieval."
      }
    ],
    "themes": [ /* Themes array matching above */ ],
    "agreements": ["Consensus that retriever precision is more critical than recall."],
    "differences": ["Optimal retrieval granularities: sentence-level vs paragraph-level."],
    "contradictions": ["Trade-off between retrieval latency and factuality gains."],
    "methodological_differences": ["Dense vector embeddings vs hybrid BM25 + ColBERT."],
    "trends": ["Transition from static retrieval to agentic self-reflective loops."],
    "research_gaps": ["Real-time factual synchronization in streaming domains."],
    "narrative_summary": "Retrieval-Augmented Generation (RAG) has emerged as the definitive paradigm..."
  },
  "reflection": {
    "coverage_score": 0.90,
    "relevance_score": 0.92,
    "missing_topics": [],
    "weak_areas": [],
    "contradictions": [],
    "outdated_areas": [],
    "recommended_queries": [],
    "should_replan": false,
    "reason": "Exhaustive coverage achieved across theoretical architectures and benchmarks.",
    "evaluation_type": "llm_critic"
  },
  "final_review": {
    "title": "Literature Review: How does retrieval augmented generation improve factuality in large language models?",
    "narrative": "Retrieval-Augmented Generation (RAG) has emerged as...",
    "key_themes": [ ... ],
    "consensus_findings": [ ... ],
    "open_research_gaps": [ ... ],
    "coherence_score": 1.00,
    "relevance_score": 0.89
  },
  "coverage_score": 0.90,
  "stop_reason": "target_coverage_reached",
  "events": [ /* Chronological array of AgentEvent objects */ ],
  "metadata": {
    "coherence_score": 1.0,
    "average_relevance": 0.89,
    "total_papers_retrieved": 8,
    "relevant_papers_retained": 7,
    "citation_metrics": {
      "total_citations": 9855,
      "mean_citations": 1407.86,
      "median_citations": 410.0,
      "max_citations": 4820,
      "papers_with_citation_data": 7
    },
    "completed_iterations": 2
  }
}
```

---

## 5. Event Stream Schema (`AgentEvent`)

For building the Agent Trace UI or streaming status over WebSockets / Server-Sent Events (SSE):

```python
class AgentEvent(BaseModel):
    id: str                 # UUID4
    type: str               # Canonical event identifier
    iteration: int          # 1-indexed iteration (0 for initialization)
    message: str            # Human-readable progress message
    timestamp: datetime     # ISO-8601 UTC timestamp
    metadata: dict[str, Any]# Contextual metadata (counts, error details, query lists)
```

### Event Lifecycle Table

| Event Type | Typical Origin | Example Payload / Metadata |
| :--- | :--- | :--- |
| `research.started` | Orchestrator init | `{"max_iterations": 3, "target_coverage": 0.85}` |
| `planner.started` | PlanningAgent | `{}` |
| `planner.completed` | PlanningAgent | `{"query_count": 5, "sub_questions": [...]}` |
| `retrieval.started` | MultiRetriever | `{"queries": [...]}` |
| `retrieval.completed` | MultiRetriever | `{"raw_count": 108}` |
| `retrieval.failed` | MultiRetriever | `{"source": "semantic_scholar", "error": "Timeout"}` |
| `filter.completed` | RelevanceFilter | `{"total_relevant": 7, "new_relevant": 7}` |
| `synthesis.started` | SynthesisAgent | `{"paper_count": 7}` |
| `synthesis.completed`| SynthesisAgent | `{"theme_count": 2}` |
| `reflection.started` | CriticAgent | `{}` |
| `reflection.completed`| CriticAgent | `{"coverage_score": 0.65, "should_replan": true}` |
| `replanning.started` | ReplanningAgent | `{"missing_topics": [...]}` |
| `replanning.completed`| ReplanningAgent | `{"new_queries": [...]}` |
| `research.completed` | Orchestrator | `{"coverage_score": 0.90, "stop_reason": "target_coverage_reached"}` |
| `research.failed` | Orchestrator | `{"error": "..."}` |

---

## 6. Stopping Conditions & Rationale

The engine automatically halts and records one of these canonical `stop_reason` values:

1. `"target_coverage_reached"`: `state.coverage_score >= config.target_coverage`.
2. `"critic_satisfied_coverage"`: Critic explicitly determined `should_replan=False`.
3. `"diminishing_returns_no_new_papers"`: An iteration yielded fewer than `config.min_new_relevant_papers` new papers.
4. `"max_iterations_reached"`: Iteration count reached `config.max_iterations`.
5. `"error: <details>"`: Catastrophic unrecoverable error (partial result still returned).

---

## 7. Error Handling & Provider Resilience

- **Academic Provider Failure Isolation:** If Semantic Scholar or arXiv suffers rate limits (HTTP 429) or timeouts, the engine retries with exponential backoff. If retries exhaust, it logs the failure, emits `retrieval.failed`, and continues smoothly with results from the remaining providers.
- **LLM Structured Output Recovery:** If an LLM returns malformed JSON, `LLMProvider.generate_structured` automatically catches the validation error, extracts JSON from code fences or raw text, and issues a schema-guided recovery prompt to the LLM.
- **Fail-Safe Fallbacks:** Every agent (Planner, Synthesizer, Critic, Replanner, Filter) includes built-in fallback heuristics to guarantee the pipeline never crashes mid-loop.

---

## 8. Mock Mode (`RESEARCHLOOP_MODE=mock`)

Member 2 can develop and test the API, database migrations, Celery/Redis tasks, and Next.js UI **completely offline with zero credentials**.

### Enabling Mock Mode

Set in `.env`:
```ini
RESEARCHLOOP_MODE=mock
```
Or pass dynamically in code:
```python
config = ResearchConfig(mock_mode=True)
result = await engine.run("How does RAG improve factuality?", config=config)
```

In Mock Mode:
- No outbound HTTP requests are made.
- Realistic papers from `MOCK_CORPUS` (Lewis et al. NeurIPS 2020, Karpukhin et al. DPR, Min et al. FactScore, Chen et al. RGB Benchmark) are returned.
- Iteration 1 returns ~65% coverage and flags missing benchmark topics; Iteration 2 addresses the gaps and achieves ~90% coverage.
- Execution completes in < 1 second.

---

## 9. Evaluation Metrics

Member 2 can import evaluation metrics from `backend.agent.evaluation`:

```python
from backend.agent.evaluation import (
    compute_coverage,
    compute_relevance,
    compute_paper_recall,
    compute_topic_coverage,
    compute_citation_distribution,
    compute_coherence,
    CuratedBenchmarkReview,
    compare_against_benchmark,
)
```

- `compute_coherence(synthesis: Synthesis) -> float`: Evaluates theme-to-paper grounding, substantive depth, dialectical balance, and narrative completeness (0.0 to 1.0).
- `compare_against_benchmark(result: ResearchResult, benchmark: CuratedBenchmarkReview) -> BenchmarkComparisonResult`: Measures recall against curated ground-truth literature reviews.

---

## 10. CLI Development Runner

Member 2 can verify the engine directly from the command line:

```bash
python -m backend.agent.cli "How does retrieval augmented generation improve factuality in large language models?" --mock
```

To output full JSON:
```bash
python -m backend.agent.cli "How does retrieval augmented generation improve factuality in large language models?" --mock --json-output
```
