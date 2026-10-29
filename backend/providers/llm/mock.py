"""
Deterministic Mock LLM Provider for offline execution and testing.
Provides realistic academic responses for all agent roles without requiring external API keys.
"""

from __future__ import annotations

import json
import re
from typing import TypeVar, Any
from pydantic import BaseModel

from backend.providers.llm.base import LLMProvider
from backend.agent.core.config import get_settings
from backend.agent.models.search import SearchPlan
from backend.agent.models.synthesis import Synthesis, Theme, PaperAnalysis
from backend.agent.models.reflection import Reflection

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """Deterministic mock provider providing high-fidelity academic responses."""

    def __init__(self, model: str | None = "mock-gpt-4o", temperature: float = 0.0):
        super().__init__(model=model, temperature=temperature)
        self.call_history: list[dict[str, Any]] = []

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any
    ) -> str:
        """Return generic or context-specific text."""
        self.call_history.append({"prompt": prompt, "system_prompt": system_prompt})
        return "Mock LLM text completion."

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
        max_retries: int = 2,
        **kwargs: Any
    ) -> T:
        """Produce structured mock responses mapped to the requested schema."""
        self.call_history.append({
            "prompt": prompt,
            "response_model": response_model.__name__,
            "system_prompt": system_prompt
        })

        # 1. SearchPlan generation (Planner or Replanner)
        if issubclass(response_model, SearchPlan):
            return self._mock_search_plan(prompt, response_model)

        # 2. Reflection generation (Critic)
        if issubclass(response_model, Reflection):
            return self._mock_reflection(prompt, response_model)

        # 3. Synthesis generation (Synthesizer)
        if issubclass(response_model, Synthesis):
            return self._mock_synthesis(prompt, response_model)

        # 4. Relevance evaluation
        if "is_relevant" in response_model.model_fields:
            return self._mock_relevance(prompt, response_model)

        # 5. Generic fallback matching model schema
        schema_defaults = {}
        for name, field in response_model.model_fields.items():
            if field.annotation == str:
                schema_defaults[name] = f"Mock {name}"
            elif field.annotation == list[str]:
                schema_defaults[name] = [f"Mock {name} 1", f"Mock {name} 2"]
            elif field.annotation == float:
                schema_defaults[name] = 0.8
            elif field.annotation == int:
                schema_defaults[name] = 1
            elif field.annotation == bool:
                schema_defaults[name] = True
            elif field.annotation == list:
                schema_defaults[name] = []
            else:
                schema_defaults[name] = None
        return response_model.model_validate(schema_defaults)

    def _mock_search_plan(self, prompt: str, model_cls: type[T]) -> T:
        is_replanning = "critic_feedback" in prompt or "previously_executed_queries" in prompt
        settings = get_settings()
        preferred = list(settings.preferred_sources)

        if is_replanning:
            # Replanner output targeting missing benchmarks & evaluation
            data = {
                "research_question": self._extract_tag(prompt, "research_question") or "Research Question",
                "sub_questions": [
                    "How are RAG hallucination rates empirically quantified across standard benchmarks?",
                    "What are the latency-accuracy trade-offs between dense vs hybrid retrieval?",
                    "How do reranking models impact factual precision in long-context generators?"
                ],
                "keywords": [
                    "RAG benchmarks",
                    "RGB benchmark",
                    "factuality metrics",
                    "hallucination quantification",
                    "dense vs hybrid retrieval",
                    "cross-encoder reranking"
                ],
                "search_queries": [
                    '"retrieval-augmented generation" hallucination evaluation benchmark',
                    '"measuring factuality" large language models RAG',
                    '"dense hybrid retrieval" RAG accuracy comparison',
                    '"RAG evaluation metrics" precision hallucination'
                ],
                "preferred_sources": preferred,
                "min_publication_year": settings.default_min_publication_year,
                "date_range": {"start_year": 2021, "end_year": 2026},
                "inclusion_criteria": [
                    "Peer-reviewed or preprint studies with empirical benchmark evaluation",
                    "Direct measurement of factuality, groundedness, or hallucination reduction"
                ],
                "exclusion_criteria": [
                    "Unsubstantiated opinion papers",
                    "Studies lacking quantitative comparison or evaluation metrics"
                ]
            }
        else:
            # Initial Planner output
            question = self._extract_tag(prompt, "research_question") or "How does retrieval augmented generation improve factuality in large language models?"
            data = {
                "research_question": question,
                "sub_questions": [
                    "What architectural paradigms connect neural retrievers to generative language models?",
                    "How does external knowledge grounding suppress parametric hallucinations in LLMs?",
                    "What empirical metrics and benchmarks exist for assessing factual accuracy in RAG systems?",
                    "What are the failure modes and noise sensitivity limitations of retrieval-augmented generation?"
                ],
                "keywords": [
                    "retrieval augmented generation",
                    "RAG",
                    "factuality",
                    "hallucination reduction",
                    "parametric knowledge",
                    "dense retrieval",
                    "knowledge grounding"
                ],
                "search_queries": [
                    '"retrieval-augmented generation" factuality large language models',
                    '"knowledge grounding" hallucination reduction',
                    '"evaluating factual consistency" retrieval augmented generation',
                    '"dense passage retrieval" LLM empirical evaluation',
                    '"noise robustness" RAG systems failure modes'
                ],
                "preferred_sources": preferred,
                "min_publication_year": settings.default_min_publication_year,
                "date_range": {"start_year": settings.default_min_publication_year, "end_year": 2026} if settings.default_min_publication_year else None,
                "inclusion_criteria": [
                    "Focuses directly on retrieval-augmented generation (RAG) and language models",
                    "Investigates factual accuracy, hallucination reduction, or knowledge grounding",
                    "Presents empirical architecture, benchmark evaluations, or theoretical analysis",
                    f"Published in {settings.default_min_publication_year} or later" if settings.default_min_publication_year else "Peer-reviewed literature"
                ],
                "exclusion_criteria": [
                    "Studies solely focused on standalone database retrieval without generative models",
                    "Non-scholarly blog posts or position pieces lacking empirical basis",
                    f"Published prior to {settings.default_min_publication_year}" if settings.default_min_publication_year else "Non-scholarly or unverified sources"
                ]
            }
        return model_cls.model_validate(data)

    def _mock_reflection(self, prompt: str, model_cls: type[T]) -> T:
        # Determine iteration from prompt
        match = re.search(r"Iteration (\d+)", prompt)
        iteration = int(match.group(1)) if match else 1

        if iteration == 1:
            data = {
                "coverage_score": 0.65,
                "relevance_score": 0.88,
                "missing_topics": [
                    "Standardized quantitative evaluation benchmarks for factuality (e.g., RGB, FactScore)",
                    "Comparative trade-offs between sparse, dense, and hybrid retrieval mechanisms",
                    "Robustness against misleading or irrelevant retrieved passages"
                ],
                "weak_areas": [
                    "Empirical error analysis of generator hallucinations despite correct passage retrieval"
                ],
                "contradictions": [
                    "Conflicting findings on whether larger context windows diminish the necessity of RAG"
                ],
                "outdated_areas": [
                    "Early 2020 DPR foundations need pairing with modern 2023-2025 multi-hop RAG studies"
                ],
                "recommended_queries": [
                    '"retrieval augmented generation" hallucination evaluation benchmark',
                    '"measuring factuality" large language models RAG',
                    '"dense hybrid retrieval" RAG accuracy comparison'
                ],
                "should_replan": True,
                "reason": "Foundational RAG concepts and mechanisms are well-covered, but rigorous standardized benchmark evaluation and hybrid architectural comparisons remain under-represented.",
                "evaluation_type": "llm_critic"
            }
        else:
            data = {
                "coverage_score": 0.90,
                "relevance_score": 0.92,
                "missing_topics": [],
                "weak_areas": [],
                "contradictions": [
                    "Trade-off between retrieval latency and factuality gains remains active tension"
                ],
                "outdated_areas": [],
                "recommended_queries": [],
                "should_replan": False,
                "reason": "Exhaustive coverage achieved across theoretical architectures, empirical hallucination metrics, benchmark evaluations, and failure modes.",
                "evaluation_type": "llm_critic"
            }
        return model_cls.model_validate(data)

    def _mock_synthesis(self, prompt: str, model_cls: type[T]) -> T:
        # A local mock must not manufacture scientific findings. It returns only
        # exact abstract text and leaves cross-paper conclusions empty.
        blocks = re.findall(
            r'<untrusted_academic_content id="([^"]+)">\s*Title: ([^\n]+)[\s\S]*?Abstract:\n([\s\S]*?)\n</untrusted_academic_content>',
            prompt,
        )
        analyses = [
            PaperAnalysis(
                paper_id=pid,
                title=title,
                research_problem="Not established by the deterministic mock.",
                methodology="Not reported by the deterministic mock.",
                dataset=None,
                key_findings=[abstract] if abstract and abstract != "Abstract not provided." else [],
                contribution="No contribution assessment generated by the deterministic mock.",
                limitations=[],
                relevance="Paper retrieved for relevance review; substantive relevance requires model or human assessment.",
                evidence_level="abstract_only" if abstract and abstract != "Abstract not provided." else "metadata_only",
                supporting_evidence=[abstract] if abstract and abstract != "Abstract not provided." else [],
            )
            for pid, title, abstract in blocks
        ]
        abstract_rows = [row for row in analyses if row.supporting_evidence]
        evidence_themes = ([
            Theme(
                id="theme-abstract-evidence",
                title="Retrieved abstract evidence (not thematically interpreted)",
                description="These are source excerpts grouped for inspection. Mock mode does not infer shared findings or thematic relationships.",
                paper_ids=[analysis.paper_id for analysis in abstract_rows],
                key_findings=[analysis.supporting_evidence[0] for analysis in abstract_rows],
            )
        ] if abstract_rows else [])
        return model_cls.model_validate({
            "paper_analyses": analyses,
            "themes": evidence_themes,
            "agreements": [],
            "differences": [],
            "contradictions": [],
            "methodological_differences": [],
            "trends": [],
            "research_gaps": [],
            "narrative_summary": (
                f"The deterministic mock received {len(analyses)} retrieved paper records and does not infer substantive literature conclusions. "
                "It exposes abstract-level source text only."
            ),
            "quality_warnings": ["Mock mode does not perform substantive literature synthesis."],
        })

    def _mock_relevance(self, prompt: str, model_cls: type[T]) -> T:
        # Determine if paper is on-topic based on prompt content
        prompt_lower = prompt.lower()
        off_topic_markers = [
            "quantum biology", "agriculture", "crop yield", "photosynthetic",
            "algae", "soil chemistry", "marine biology", "nitrogen fixation"
        ]
        is_off_topic = any(m in prompt_lower for m in off_topic_markers)
        if is_off_topic:
            return model_cls.model_validate({
                "is_relevant": False,
                "relevance_score": 0.15,
                "relevance_reason": "The paper focuses on unrelated disciplinary concepts without investigating language models or retrieval."
            })
        return model_cls.model_validate({
            "is_relevant": True,
            "relevance_score": 0.89,
            "relevance_reason": "The paper directly addresses retrieval-augmented architectures and factual consistency in generative models."
        })

    def _extract_tag(self, text: str, tag: str) -> str | None:
        match = re.search(rf"<{tag}>([\s\S]*?)</{tag}>", text)
        return match.group(1).strip() if match else None
