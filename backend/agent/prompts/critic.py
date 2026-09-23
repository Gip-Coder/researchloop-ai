"""
Critic / Self-reflection agent prompt templates.
"""

from __future__ import annotations
from typing import Any
from backend.agent.models.search import SearchPlan
from backend.agent.models.synthesis import Synthesis
from backend.agent.models.paper import Paper


CRITIC_SYSTEM_PROMPT = """You are the Senior Critic and Self-Reflection Agent for researchloop-ai.
Your role is to rigorously evaluate the current state of literature review synthesis and decide whether additional iterations are needed.

Evaluation Dimensions:
1. Coverage: Has every key sub-question and conceptual facet of the research question been addressed with substantive evidence?
2. Relevance: Are the reviewed papers truly focused on the core inquiry, or has retrieval drifted into tangential topics?
3. Recency: Are the latest developments, benchmarks, or architectures adequately represented?
4. Diversity: Are distinct methodologies, institutions, and experimental frameworks present?
5. Contradictions & Nuance: Has conflicting or nuanced empirical evidence been investigated, or is the synthesis one-sided?
6. Missing Topics: What essential areas, sub-questions, or evaluation benchmarks remain completely unrepresented?
7. Evidence Quality: Are the conclusions substantiated by concrete experimental data?

Decision:
- If coverage is high (e.g. >= 0.85) and key dimensions are satisfied, set should_replan=False.
- If major topics are missing or evidence is shallow, set should_replan=True and generate recommended_queries targeting the specific gaps.
"""


def build_critic_prompt(
    research_question: str,
    search_plan: SearchPlan | None,
    relevant_papers: list[Paper],
    synthesis: Synthesis | None,
    iteration: int
) -> str:
    sub_qs = "\n".join(f"- {q}" for q in (search_plan.sub_questions if search_plan else [])) or "None"
    paper_titles = "\n".join(f"- [{p.year or 'N/A'}] {p.title}" for p in relevant_papers[:25]) or "None"
    themes_summary = "\n".join(f"- {t.title}: {t.description}" for t in (synthesis.themes if synthesis else [])) or "None"
    gaps_summary = "\n".join(f"- {g}" for g in (synthesis.research_gaps if synthesis else [])) or "None"

    return f"""Perform an exhaustive critical evaluation of the research synthesis (Iteration {iteration}):

<research_question>
{research_question}
</research_question>

<planned_sub_questions>
{sub_qs}
</planned_sub_questions>

<retrieved_corpus_sample count="{len(relevant_papers)}">
{paper_titles}
</retrieved_corpus_sample>

<synthesized_themes>
{themes_summary}
</synthesized_themes>

<noted_gaps_in_synthesis>
{gaps_summary}
</noted_gaps_in_synthesis>

Provide a rigorous evaluation:
1. coverage_score (0.0 to 1.0)
2. relevance_score (0.0 to 1.0)
3. missing_topics (list of specific unaddressed sub-topics)
4. weak_areas (list of areas lacking strong evidence)
5. contradictions (list of conflicting points needing deeper inspection)
6. outdated_areas (areas lacking recent literature)
7. recommended_queries (3 to 6 precise academic search queries targeting the gaps)
8. should_replan (boolean: true if gaps require another retrieval cycle)
9. reason (detailed justification for this assessment)
"""
