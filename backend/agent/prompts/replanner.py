"""
Replanning agent prompt templates.
"""

from __future__ import annotations
from typing import Any
from backend.agent.models.search import SearchPlan
from backend.agent.models.reflection import Reflection


REPLANNER_SYSTEM_PROMPT = """You are the Senior Replanning Agent for researchloop-ai.
Your responsibility is to adjust and refocus the research strategy based on the Critic's reflection and identified literature gaps.

Key Principles:
1. Do NOT repeat search queries that have already been executed.
2. Directly convert the Critic's missing topics and weak areas into targeted academic search phrases.
3. Formulate phrase-based queries combining multiword exact phrases enclosed in double quotes with specific gap concepts (e.g., '"retrieval-augmented generation" "hallucination evaluation"', '"dense passage retrieval" noise robustness'). Avoid isolated generic single words.
4. Refine inclusion/exclusion criteria if needed.
5. Prioritize modern literature published in 2019 or later.
6. Output a revised, actionable SearchPlan for the next iteration.
"""


def build_replanner_prompt(
    research_question: str,
    previous_plan: SearchPlan,
    prior_queries: list[str],
    reflection: Reflection
) -> str:
    prior_queries_str = "\n".join(f"- {q}" for q in prior_queries) or "None"
    missing_str = "\n".join(f"- {m}" for m in reflection.missing_topics) or "None"
    weak_str = "\n".join(f"- {w}" for w in reflection.weak_areas) or "None"
    rec_queries_str = "\n".join(f"- {r}" for r in reflection.recommended_queries) or "None"

    return f"""Formulate a revised search plan to address the literature gaps identified by the Critic:

<research_question>
{research_question}
</research_question>

<critic_feedback reason="{reflection.reason}">
Coverage Score: {reflection.coverage_score:.2f}
Missing Topics:
{missing_str}

Weak Areas:
{weak_str}

Critic Recommended Queries:
{rec_queries_str}
</critic_feedback>

<previously_executed_queries>
{prior_queries_str}
</previously_executed_queries>

Generate a revised SearchPlan containing:
1. sub_questions: updated list focusing on the unresolved dimensions
2. keywords: new academic terminology targeting the missing concepts
3. search_queries: 4 to 8 brand new phrase-based search queries with multiword quotes, targeting the gaps and distinct from previously executed queries
4. preferred_sources: list of sources (default: ["arxiv", "crossref"])
5. min_publication_year: 2019
6. date_range: start_year >= 2019
"""
