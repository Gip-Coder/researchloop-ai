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
                "date_range": {"start_year": settings.default_min_publication_year, "end_year": 2026},
                "inclusion_criteria": [
                    "Focuses directly on retrieval-augmented generation (RAG) and language models",
                    "Investigates factual accuracy, hallucination reduction, or knowledge grounding",
                    "Presents empirical architecture, benchmark evaluations, or theoretical analysis",
                    f"Published in {settings.default_min_publication_year} or later"
                ],
                "exclusion_criteria": [
                    "Studies solely focused on standalone database retrieval without generative models",
                    "Non-scholarly blog posts or position pieces lacking empirical basis",
                    f"Published prior to {settings.default_min_publication_year}"
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
        # Parse papers embedded inside <untrusted_academic_content>
        paper_blocks = re.findall(
            r'<untrusted_academic_content id="([^"]+)">\s*Title: ([^\n]+)',
            prompt
        )

        analyses = []
        paper_ids = []
        for pid, ptitle in paper_blocks:
            paper_ids.append(pid)
            analyses.append(
                PaperAnalysis(
                    paper_id=pid,
                    title=ptitle,
                    research_problem="Mitigating hallucinations and factual drift in LLM text generation.",
                    methodology="Dual-encoder dense retrieval integrated with cross-attention generative decoder.",
                    dataset="NaturalQuestions, HotpotQA, and FactScore benchmarks.",
                    key_findings=[
                        "External document retrieval reduces factual errors by 32% compared to closed-book generators.",
                        "Precision of top-1 passage is the primary determinant of factual integrity."
                    ],
                    contribution="End-to-end framework coupling parametric and non-parametric memory.",
                    limitations=[
                        "Susceptible to distraction when retrieved documents contain conflicting claims."
                    ],
                    relevance="Directly demonstrates mechanism of factual grounding via external retrieval."
                )
            )

        # Distribute paper_ids across thematic clusters
        half = max(1, len(paper_ids) // 2)
        theme1_ids = paper_ids[:half] if paper_ids else ["p1", "p2", "p3"]
        theme2_ids = paper_ids[half:] if paper_ids else ["p4", "p5", "p6"]

        themes = [
            Theme(
                id="theme-1",
                title="Grounding Generative Outputs in Non-Parametric Memory",
                description="Core architectural research focusing on coupling pre-trained language models with external vector databases to provide verifiably cited passages.",
                paper_ids=theme1_ids,
                key_findings=[
                    "Non-parametric grounding significantly lowers hallucinations on knowledge-intensive QA.",
                    "Attribution accuracy improves when passages are reranked prior to generation."
                ],
                contradictions_or_tensions=[
                    "Debate over whether fine-tuning generator on retrieved noise is superior to strict zero-shot prompting."
                ]
            ),
            Theme(
                id="theme-2",
                title="Empirical Benchmarks and Hallucination Quantification",
                description="Studies developing diagnostic datasets to measure factual precision, knowledge conflicts, and noise sensitivity in RAG systems.",
                paper_ids=theme2_ids,
                key_findings=[
                    "Standard accuracy metrics mask subtle hallucinations; token-level attribution (FactScore) is required.",
                    "Generators often succumb to primacy bias when multiple retrieved documents disagree."
                ],
                contradictions_or_tensions=[
                    "Varying definitions of what constitutes acceptable factual hallucination across technical vs conversational domains."
                ]
            )
        ]

        data = {
            "paper_analyses": analyses,
            "themes": themes,
            "agreements": [
                "Broad empirical evidence across studies indicates that retrieval augmentation consistently improves factual accuracy over closed-book models on dynamic and long-tail knowledge tasks.",
                "Studies converge on the finding that retriever precision is more critical than retriever recall for minimizing generator hallucination rates."
            ],
            "differences": [
                "Divergence in optimal retrieval granularities: sentence-level vs paragraph-level chunks.",
                "Different conclusions regarding the utility of multi-hop retrieval for single-step factual queries."
            ],
            "contradictions": [
                "Some studies claim reranking eliminates noise degradation, whereas others show generators still misinterpret ambiguous top-ranked snippets."
            ],
            "methodological_differences": [
                "Dense vector embeddings (DPR/Contriever) vs hybrid lexical-dense index (BM25 + ColBERT).",
                "Prompt-based in-context RAG vs end-to-end differentiable backpropagation across retriever and reader."
            ],
            "trends": [
                "Transition from static pre-retrieval to iterative, agentic, and self-reflective retrieval loops.",
                "Increasing adoption of fine-grained attribution metrics over traditional BLEU/ROUGE overlap."
            ],
            "research_gaps": [
                "Real-time factual synchronization in high-velocity streaming domains.",
                "Robust resolution of contradictory claims across heterogeneous web sources."
            ],
            "narrative_summary": (
                f"Synthesized evidence from {len(paper_ids)} eligible peer-reviewed works (2019+). "
                "Retrieval-Augmented Generation (RAG) has emerged as a leading paradigm for reducing "
                "parametric hallucinations and enforcing factual grounding in Large Language Models. By decomposing "
                "knowledge access into non-parametric retrieval and generative reasoning, RAG systems ground outputs "
                "in verifiable external evidence. Current open frontiers center on noise robustness, multi-hop "
                "reasoning, and nuanced contradiction resolution when retrieved literature conflicts."
            )
        }
        return model_cls.model_validate(data)

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
