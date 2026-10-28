"""
Benchmark script comparing retrieval performance between:
Configuration A: PREFERRED_SOURCES=arxiv,crossref
Configuration B: PREFERRED_SOURCES=arxiv,crossref,semantic_scholar

Measures:
- Median retrieval latency across trials
- Number of candidate papers retrieved
- Failure / timeout / rate-limit counts
- Evidence quality observations
"""

import asyncio
import time
import statistics
from backend.agent.core.config import get_settings
from backend.agent.retrieval.multi_retriever import MultiProviderRetriever
from backend.agent.retrieval.arxiv import ArxivProvider
from backend.agent.retrieval.crossref import CrossrefProvider
from backend.agent.retrieval.semantic_scholar import SemanticScholarProvider
from backend.agent.models.search import SearchPlan, DateRange


QUERIES = [
    ['"retrieval-augmented generation" evaluation benchmark'],
    ['"graph neural networks" scalability large graphs'],
    ['"contrastive learning" visual representation'],
]


async def run_trials(config_name: str, providers_list: list, preferred_sources: list[str], runs_per_query: int = 2):
    print(f"\n==========================================")
    print(f"Running Benchmark: {config_name}")
    print(f"Active Providers: {[p.name for p in providers_list]}")
    print(f"==========================================")

    # Disable cache to measure actual network/API latency on every trial
    retriever = MultiProviderRetriever(providers=providers_list, cache_enabled=False)
    durations = []
    total_candidates = []
    error_count = 0

    for q_idx, queries in enumerate(QUERIES, 1):
        plan = SearchPlan(
            research_question=queries[0],
            sub_questions=[],
            search_queries=queries,
            preferred_sources=preferred_sources,
            min_publication_year=2019,
        )
        for run_idx in range(runs_per_query):
            start_t = time.perf_counter()
            try:
                papers = await retriever.retrieve_for_plan(plan, iteration=1)
                dur = time.perf_counter() - start_t
                durations.append(dur)
                total_candidates.append(len(papers))
                print(f"  [Q{q_idx} Run {run_idx+1}] Query: '{queries[0][:40]}...' -> {len(papers)} papers in {dur:.2f}s")
            except Exception as e:
                dur = time.perf_counter() - start_t
                error_count += 1
                durations.append(dur)
                print(f"  [Q{q_idx} Run {run_idx+1}] Query failed after {dur:.2f}s with error: {type(e).__name__}: {e}")

    # Close providers
    for p in providers_list:
        if hasattr(p, "close"):
            await p.close()

    median_lat = statistics.median(durations) if durations else 0.0
    mean_lat = statistics.mean(durations) if durations else 0.0
    avg_papers = statistics.mean(total_candidates) if total_candidates else 0

    print(f"\nSummary for {config_name}:")
    print(f"  - Completed runs: {len(durations)}")
    print(f"  - Errors / Timeouts: {error_count}")
    print(f"  - Median Latency: {median_lat:.2f}s")
    print(f"  - Mean Latency: {mean_lat:.2f}s")
    print(f"  - Avg Papers Retrieved: {avg_papers:.1f}")

    return {
        "config": config_name,
        "sources": preferred_sources,
        "median_latency": median_lat,
        "mean_latency": mean_lat,
        "avg_papers": avg_papers,
        "errors": error_count,
        "durations": durations,
    }


async def main():
    print("Starting ResearchLoop AI Retrieval Source Benchmark...")

    # Config A: ArXiv + Crossref (Default)
    providers_a = [
        ArxivProvider(timeout=10, max_retries=1),
        CrossrefProvider(timeout=10, max_retries=1),
    ]
    res_a = await run_trials(
        "Configuration A (arxiv,crossref)",
        providers_a,
        ["arxiv", "crossref"],
        runs_per_query=2
    )

    # Config B: ArXiv + Crossref + Semantic Scholar
    providers_b = [
        ArxivProvider(timeout=10, max_retries=1),
        CrossrefProvider(timeout=10, max_retries=1),
        SemanticScholarProvider(timeout=10, max_retries=1),
    ]
    res_b = await run_trials(
        "Configuration B (arxiv,crossref,semantic_scholar)",
        providers_b,
        ["arxiv", "crossref", "semantic_scholar"],
        runs_per_query=2
    )

    print("\n==========================================")
    print("COMPARATIVE BENCHMARK RESULTS")
    print("==========================================")
    diff = res_b["median_latency"] - res_a["median_latency"]
    pct = ((res_b["median_latency"] - res_a["median_latency"]) / res_b["median_latency"] * 100) if res_b["median_latency"] > 0 else 0
    print(f"Config A (arxiv,crossref) Median Latency: {res_a['median_latency']:.2f}s")
    print(f"Config B (arxiv,crossref,semantic_scholar) Median Latency: {res_b['median_latency']:.2f}s")
    print(f"Latency Difference: {diff:+.2f}s ({pct:.1f}% reduction in Config A)")
    print(f"Config A Avg Papers: {res_a['avg_papers']:.1f}")
    print(f"Config B Avg Papers: {res_b['avg_papers']:.1f}")
    print(f"Config A Errors: {res_a['errors']}")
    print(f"Config B Errors: {res_b['errors']}")


if __name__ == "__main__":
    asyncio.run(main())
