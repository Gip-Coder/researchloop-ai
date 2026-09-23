"""
Standalone CLI development runner for Member 1 testing.
Usage:
    python -m backend.agent.cli "How does retrieval augmented generation improve factuality in large language models?" --mock
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from backend.agent.orchestration.engine import ResearchEngine
from backend.agent.models.research import ResearchConfig
from backend.agent.models.common import AgentEvent


def format_cli_output(event: AgentEvent) -> None:
    """Pretty-print events to stdout for real-time progress using console-safe symbols."""
    tag_map = {
        "research.started": "[START]",
        "planner.started": "[PLAN]",
        "planner.completed": "[PLAN_OK]",
        "retrieval.started": "[RETRIEVE]",
        "retrieval.completed": "[RETRIEVE_OK]",
        "retrieval.failed": "[RETRIEVE_WARN]",
        "filter.completed": "[FILTER]",
        "synthesis.started": "[SYNTHESIZE]",
        "synthesis.completed": "[SYNTHESIZE_OK]",
        "reflection.started": "[REFLECT]",
        "reflection.completed": "[CRITIC]",
        "replanning.started": "[REPLAN]",
        "replanning.completed": "[REPLAN_OK]",
        "research.completed": "[COMPLETE]",
        "research.failed": "[FAILED]"
    }
    tag = tag_map.get(event.type, "[EVENT]")
    print(f"[{event.iteration}] {tag:<15} {event.message}")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="researchloop-ai — Autonomous Literature Review Agent CLI"
    )
    parser.add_argument(
        "question",
        type=str,
        help="Scientific research question to investigate"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        default=True,
        help="Run in deterministic mock mode (default: True)"
    )
    parser.add_argument(
        "--live",
        dest="mock",
        action="store_false",
        help="Run against real live LLMs and academic APIs"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum iterations (default: 3)"
    )
    parser.add_argument(
        "--target-coverage",
        type=float,
        default=0.85,
        help="Target coverage score (default: 0.85)"
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="mock",
        help="LLM provider: 'mock', 'openai', 'anthropic', 'gemini' (default: 'mock')"
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Print final ResearchResult JSON to stdout"
    )

    args = parser.parse_args()

    config = ResearchConfig(
        max_iterations=args.max_iterations,
        target_coverage=args.target_coverage,
        llm_provider=args.provider,
        mock_mode=args.mock,
        event_callback=format_cli_output
    )

    print("=" * 65)
    print("RESEARCHLOOP-AI: AUTONOMOUS LITERATURE REVIEW ENGINE")
    print("=" * 65)
    print(f"Research Question : {args.question}")
    print(f"Mode              : {'MOCK (zero credentials required)' if config.mock_mode else 'LIVE'}")
    print(f"Max Iterations    : {config.max_iterations}")
    print(f"Target Coverage   : {config.target_coverage:.1%}")
    print("-" * 65)

    engine = ResearchEngine(default_config=config)
    result = await engine.run(args.question, config=config)

    print("\n" + "=" * 65)
    print("FINAL RESEARCH RESULT")
    print("=" * 65)
    print(f"Status           : {result.status.upper()}")
    print(f"Final Coverage   : {result.coverage_score:.1%}")
    print(f"Stop Reason      : {result.stop_reason}")
    print(f"Total Papers     : {len(result.papers)} discovered ({len(result.relevant_papers)} deemed relevant)")
    print(f"Thematic Clusters: {len(result.themes)}")
    print(f"Total Iterations : {len(result.iterations)}")

    if result.synthesis and result.synthesis.narrative_summary:
        print("\nNarrative Summary:")
        print("-" * 40)
        print(result.synthesis.narrative_summary)

    if result.themes:
        print("\nKey Themes Discovered:")
        print("-" * 40)
        for i, theme in enumerate(result.themes, 1):
            print(f"{i}. {theme.title} ({len(theme.paper_ids)} papers)")
            print(f"   {theme.description[:120]}...")

    if result.metadata:
        print(f"\nCoherence Score  : {result.metadata.get('coherence_score', 0):.2f}")
        print(f"Average Relevance: {result.metadata.get('average_relevance', 0):.2f}")

    if args.json_output:
        print("\n--- JSON OUTPUT ---")
        print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    asyncio.run(main())

