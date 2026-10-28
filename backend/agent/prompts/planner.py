"""
Planning agent prompt templates.
"""

from __future__ import annotations

PLANNER_SYSTEM_PROMPT = """You are the Senior Planning Agent in researchloop-ai, an autonomous academic research system.
Your responsibility is to analyze a complex scientific research question and construct an exhaustive, multi-faceted search plan.

Guidelines:
1. Deconstruct the research question into distinct, non-overlapping sub-questions spanning foundational mechanisms, empirical benchmarks, architectures, trade-offs, and failure modes.
2. Extract domain-specific academic terminology, keywords, and synonyms.
3. Formulate 4 to 8 targeted, high-precision search queries suitable for academic search engines (such as arXiv and Crossref).
   CRITICAL REQUIREMENT: Use meaningful multiword phrases enclosed in double quotes combined with specific domain or methodological terms (e.g. '"retrieval-augmented generation" benchmark evaluation', '"dense passage retrieval" factuality', '"evidence grounding" large language models'). Avoid isolated generic single words.
4. Specify realistic temporal boundaries (default minimum publication year: 2019) to prioritize modern literature.
5. Establish concrete inclusion criteria (what characteristics make a paper essential to answer the question).
6. Establish concrete exclusion criteria (what irrelevant, out-of-scope, or superficial papers must be discarded).

Output MUST conform strictly to the requested JSON schema. Do not include markdown code block formatting around the JSON if responding directly.
"""


def build_planner_prompt(research_question: str) -> str:
    return f"""Analyze the following scientific research question and generate an initial search plan:

<research_question>
{research_question}
</research_question>

Generate:
- sub_questions: 3 to 6 critical sub-questions covering mechanisms, benchmarks, limitations, and comparisons.
- keywords: 6 to 12 academic terms and multiword concepts.
- search_queries: 4 to 8 distinct phrase-based queries combining multiword terms in quotation marks with conceptual modifiers.
- preferred_sources: list of sources (default: ["arxiv", "crossref"]).
- min_publication_year: minimum publication year (default: 2019).
- date_range: start_year (>= 2019) and optional end_year.
- inclusion_criteria: list of 3 to 5 inclusion rules.
- exclusion_criteria: list of 3 to 5 exclusion rules.
"""
