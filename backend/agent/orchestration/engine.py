"""
Autonomous research loop orchestration engine.
Connects planning, retrieval, deduplication, filtering, synthesis, critic reflection, and replanning.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Callable, Awaitable, Any

from backend.agent.core.config import get_settings
from backend.agent.models.common import AgentEvent, EventType
from backend.agent.models.paper import Paper
from backend.agent.models.search import SearchPlan
from backend.agent.models.research import (
    ResearchConfig,
    ResearchState,
    ResearchIteration,
    ResearchResult,
)
from backend.agent.planner.planner import PlanningAgent
from backend.agent.retrieval.multi_retriever import MultiProviderRetriever
from backend.agent.filtering.deduplication import Deduplicator
from backend.agent.filtering.relevance import RelevanceFilter
from backend.agent.synthesis.synthesizer import SynthesisAgent
from backend.agent.reflection.critic import CriticAgent
from backend.agent.replanning.replanner import ReplanningAgent
from backend.agent.evaluation.metrics import (
    compute_coverage,
    compute_relevance,
    compute_citation_distribution,
    compute_coherence,
)
from backend.providers.llm.factory import get_llm_provider

logger = logging.getLogger(__name__)


class ResearchEngine:
    """
    Public entry point for the researchloop-ai AI Agent Engine.
    Executes the autonomous literature review loop.
    """

    def __init__(self, default_config: ResearchConfig | None = None):
        self.default_config = default_config or ResearchConfig()

    async def run(
        self,
        research_question: str,
        config: ResearchConfig | None = None
    ) -> ResearchResult:
        """
        Execute the autonomous research loop for the given research question.
        """
        cfg = config or self.default_config
        settings = get_settings()

        # Initialize LLM provider and sub-agents
        llm = get_llm_provider(cfg)
        planner = PlanningAgent(llm_provider=llm)
        retriever = MultiProviderRetriever(mock_mode=cfg.mock_mode or settings.is_mock_mode, cache_enabled=cfg.cache_enabled)
        deduplicator = Deduplicator()
        relevance_filter = RelevanceFilter(llm_provider=llm)
        synthesizer = SynthesisAgent(llm_provider=llm)
        critic = CriticAgent(llm_provider=llm)
        replanner = ReplanningAgent(llm_provider=llm)

        # Initialize ResearchState
        session_id = str(uuid.uuid4())
        state = ResearchState(
            session_id=session_id,
            research_question=research_question,
            iteration=1,
            coverage_score=0.0
        )

        async def _emit(event_type: EventType | str, message: str, metadata: dict[str, Any] | None = None) -> None:
            t_str = event_type.value if isinstance(event_type, EventType) else str(event_type)
            evt = AgentEvent(
                type=t_str,
                iteration=state.iteration,
                message=message,
                metadata=metadata or {}
            )
            state.events.append(evt)
            if cfg.event_callback:
                try:
                    res = cfg.event_callback(evt)
                    if hasattr(res, "__await__"):
                        await res
                except Exception as cb_err:
                    logger.warning(f"Event callback error: {cb_err}")

        await _emit(
            EventType.RESEARCH_STARTED,
            f"Research loop initialized for: '{research_question}'",
            {"max_iterations": cfg.max_iterations, "target_coverage": cfg.target_coverage}
        )

        try:
            # 1. Initial Planning Phase
            await _emit(EventType.PLANNER_STARTED, "Formulating initial search plan...")
            search_plan = await planner.plan(research_question)
            state.search_plan = search_plan
            await _emit(
                EventType.PLANNER_COMPLETED,
                f"Generated search plan with {len(search_plan.search_queries)} queries.",
                {"query_count": len(search_plan.search_queries), "sub_questions": search_plan.sub_questions}
            )

            # Iterative Loop
            while state.iteration <= cfg.max_iterations:
                current_plan = state.search_plan
                queries_to_run = current_plan.search_queries

                # 2. Retrieval Phase
                await _emit(
                    EventType.RETRIEVAL_STARTED,
                    f"Retrieving literature across {current_plan.preferred_sources} for {len(queries_to_run)} queries.",
                    {"queries": queries_to_run}
                )
                raw_fetched_papers = await retriever.retrieve_for_plan(
                    plan=current_plan,
                    iteration=state.iteration,
                    event_callback=_emit
                )
                await _emit(
                    EventType.RETRIEVAL_COMPLETED,
                    f"Retrieved {len(raw_fetched_papers)} candidate paper records.",
                    {"raw_count": len(raw_fetched_papers)}
                )

                # 3. Deduplication Phase
                prior_paper_count = len(state.papers)
                state.papers = deduplicator.deduplicate(raw_fetched_papers, state.papers)
                new_unique_papers_count = len(state.papers) - prior_paper_count

                # 4. Relevance Filtering Phase
                # Evaluate candidate papers that haven't been scored yet
                unfiltered_papers = [p for p in state.papers if p.is_relevant is None]
                if unfiltered_papers:
                    newly_relevant, newly_rejected = await relevance_filter.filter_papers(unfiltered_papers, current_plan)
                    # Update state.papers with evaluation scores and reasons
                    eval_map = {p.id: p for p in newly_relevant + newly_rejected}
                    state.papers = [eval_map.get(p.id, p) for p in state.papers]
                else:
                    newly_relevant = []

                prior_relevant_count = len(state.relevant_papers)
                # Re-collate all relevant papers from state.papers
                state.relevant_papers = [p for p in state.papers if p.is_relevant is True]
                new_relevant_count = len(state.relevant_papers) - prior_relevant_count

                await _emit(
                    EventType.FILTER_COMPLETED,
                    f"Relevance filtering complete: {len(state.relevant_papers)} total relevant papers (+{new_relevant_count} new).",
                    {"total_relevant": len(state.relevant_papers), "new_relevant": new_relevant_count}
                )

                # 5. Synthesis Phase
                await _emit(
                    EventType.SYNTHESIS_STARTED,
                    f"Synthesizing {len(state.relevant_papers)} relevant papers into thematic clusters...",
                    {"paper_count": len(state.relevant_papers)}
                )
                synthesis = await synthesizer.synthesize(research_question, state.relevant_papers)
                state.synthesis = synthesis
                state.themes = synthesis.themes
                await _emit(
                    EventType.SYNTHESIS_COMPLETED,
                    f"Synthesis completed with {len(synthesis.themes)} emergent themes and narrative summary.",
                    {"theme_count": len(synthesis.themes)}
                )

                # 6. Critic / Self-Reflection Phase
                await _emit(EventType.REFLECTION_STARTED, "Evaluating synthesis coverage, relevance, and evidence depth...")
                reflection = await critic.evaluate(state)
                state.reflection = reflection
                state.coverage_score = reflection.coverage_score
                await _emit(
                    EventType.REFLECTION_COMPLETED,
                    f"Critic assessed coverage at {reflection.coverage_score:.1%}. Reason: {reflection.reason}",
                    {
                        "coverage_score": reflection.coverage_score,
                        "relevance_score": reflection.relevance_score,
                        "missing_topics": reflection.missing_topics,
                        "should_replan": reflection.should_replan
                    }
                )

                # Record Iteration History
                iteration_record = ResearchIteration(
                    iteration=state.iteration,
                    search_plan=current_plan,
                    queries_executed=queries_to_run,
                    papers_retrieved_count=len(raw_fetched_papers),
                    new_papers_count=new_unique_papers_count,
                    relevant_papers_count=len(state.relevant_papers),
                    coverage_score=reflection.coverage_score,
                    reflection=reflection,
                    timestamp=datetime.now(timezone.utc)
                )
                state.iteration_history.append(iteration_record)

                # 7. Check Stopping Conditions
                # Condition A: Target coverage reached
                if state.coverage_score >= cfg.target_coverage:
                    state.completed = True
                    state.stop_reason = "target_coverage_reached"
                    break

                # Condition B: Diminishing returns (no new relevant papers found after iteration 1)
                if state.iteration > 1 and new_relevant_count < cfg.min_new_relevant_papers:
                    state.completed = True
                    state.stop_reason = "diminishing_returns_no_new_papers"
                    break

                # Condition C: Critic is satisfied and indicates no replanning needed
                if not reflection.should_replan:
                    state.completed = True
                    state.stop_reason = "critic_satisfied_coverage"
                    break

                # Condition D: Max iterations reached
                if state.iteration >= cfg.max_iterations:
                    state.completed = True
                    state.stop_reason = "max_iterations_reached"
                    break

                # 8. Replanning Phase (if not stopping)
                await _emit(
                    EventType.REPLANNING_STARTED,
                    f"Replanning search queries to target gaps: {reflection.missing_topics[:2]}...",
                    {"missing_topics": reflection.missing_topics}
                )
                new_plan = await replanner.replan(state)
                state.search_plan = new_plan
                await _emit(
                    EventType.REPLANNING_COMPLETED,
                    f"Generated {len(new_plan.search_queries)} new targeted search queries for Iteration {state.iteration + 1}.",
                    {"new_queries": new_plan.search_queries}
                )

                state.iteration += 1

            if not state.stop_reason:
                state.stop_reason = "max_iterations_reached"
                state.completed = True

            await _emit(
                EventType.RESEARCH_COMPLETED,
                f"Research loop completed successfully. Stop reason: {state.stop_reason}. Final coverage: {state.coverage_score:.1%}.",
                {"coverage_score": state.coverage_score, "stop_reason": state.stop_reason}
            )

            return self._build_result(state, status="completed")

        except Exception as err:
            logger.exception(f"Fatal error during research execution: {err}")
            await _emit(
                EventType.RESEARCH_FAILED,
                f"Research execution encountered an unrecoverable failure: {err}",
                {"error": str(err)}
            )
            state.completed = True
            state.stop_reason = f"error: {err}"
            return self._build_result(state, status="failed")

    def _build_result(self, state: ResearchState, status: str) -> ResearchResult:
        """Construct canonical frozen ResearchResult contract."""
        coherence = compute_coherence(state.synthesis)
        avg_rel = compute_relevance(state.relevant_papers)
        citation_stats = compute_citation_distribution(state.relevant_papers)

        final_review = {
            "title": f"Literature Review: {state.research_question}",
            "narrative": state.synthesis.narrative_summary if state.synthesis else "",
            "key_themes": [
                {
                    "title": t.title,
                    "description": t.description,
                    "paper_count": len(t.paper_ids),
                    "key_findings": t.key_findings
                }
                for t in (state.themes or [])
            ],
            "consensus_findings": state.synthesis.agreements if state.synthesis else [],
            "open_research_gaps": state.synthesis.research_gaps if state.synthesis else [],
            "coherence_score": coherence,
            "relevance_score": avg_rel
        }

        return ResearchResult(
            session_id=state.session_id,
            status=status,
            research_question=state.research_question,
            iterations=state.iteration_history,
            papers=state.papers,
            relevant_papers=state.relevant_papers,
            themes=state.themes,
            synthesis=state.synthesis,
            reflection=state.reflection,
            final_review=final_review,
            coverage_score=state.coverage_score,
            stop_reason=state.stop_reason,
            events=state.events,
            metadata={
                "coherence_score": coherence,
                "average_relevance": avg_rel,
                "total_papers_retrieved": len(state.papers),
                "relevant_papers_retained": len(state.relevant_papers),
                "citation_metrics": citation_stats,
                "completed_iterations": len(state.iteration_history)
            }
        )

