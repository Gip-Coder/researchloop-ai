"""Deterministic safeguards for evidence-aware synthesis."""

import pytest

from backend.agent.filtering.ranking import rank_papers_for_synthesis
from backend.agent.models.paper import Paper
from backend.agent.models.synthesis import Synthesis, Theme, PaperAnalysis, PaperEvidence
from backend.agent.models.search import SearchPlan
from backend.agent.models.common import DateRange
from backend.agent.retrieval.base import AcademicSource
from backend.agent.retrieval.multi_retriever import MultiProviderRetriever
from backend.agent.prompts.synthesis import build_synthesis_prompt, SYNTHESIS_SYSTEM_PROMPT
from backend.agent.synthesis.synthesizer import SynthesisAgent, _has_source_for_quantities, _is_traceable_gap
from backend.providers.llm.base import LLMProvider


class BrokenProvider(LLMProvider):
    async def generate(self, *args, **kwargs):
        raise RuntimeError("deterministic fixture failure")

    async def generate_structured(self, *args, **kwargs):
        raise RuntimeError("deterministic fixture failure")


def paper(pid: str, *, year: int | None = 2022, relevance: float = 0.8, citations: int | None = None) -> Paper:
    return Paper(
        id=pid,
        title=f"Study {pid}",
        year=year,
        source="crossref",
        abstract="The abstract reports a simulated evaluation of federated learning in hospitals.",
        citation_count=citations,
        relevance_score=relevance,
        url=f"https://example.org/{pid}",
    )


@pytest.mark.asyncio
async def test_generation_failure_does_not_create_findings_or_gaps():
    agent = SynthesisAgent(BrokenProvider())
    result = await agent.synthesize("Federated learning privacy in healthcare", [paper("p1")])

    assert isinstance(result, Synthesis)
    assert result.themes
    assert any(result.evidence_matrix[0].paper_id in theme.paper_ids for theme in result.themes)
    assert result.agreements == []
    assert result.research_gaps == []
    assert "generation failed" in result.quality_warnings[0].lower()
    assert result.evidence_matrix[0].evidence_level == "abstract_only"
    assert result.evidence_matrix[0].privacy_mechanism is None
    assert result.evidence_matrix[0].healthcare_relevance == "Direct healthcare context is stated in the abstract."


def test_synthesis_prompt_marks_abstract_only_and_unknown_citations():
    prompt = build_synthesis_prompt("FL privacy", [paper("p1", citations=None)])

    assert "Citations: Unknown" in prompt
    assert "full text was not supplied" in prompt
    assert "Do not infer methods" in SYNTHESIS_SYSTEM_PROMPT


def test_rank_prefers_relevance_and_keeps_unknown_citations_unknown():
    relevant = paper("high-relevance", relevance=0.99, citations=500)
    preferred = paper("preferred-citations", relevance=0.7, citations=12)
    unknown = paper("unknown-citations", relevance=0.8, citations=None)

    ranked, excluded = rank_papers_for_synthesis([preferred, relevant, unknown], min_year=2019)

    assert not excluded
    assert ranked[0].id == "high-relevance"
    old, rejected = rank_papers_for_synthesis([paper("historical", year=1899)], min_year=2019)
    assert [item.id for item in old] == ["historical"]
    assert rejected == []
    assert next(p for p in ranked if p.id == "unknown-citations").citation_count is None


def test_unsupported_quantitative_claim_is_rejected():
    source = paper("p1")
    assert not _has_source_for_quantities("Accuracy improved by 32%.", [source])
    assert _has_source_for_quantities("The abstract reports a simulated evaluation.", [source])


def test_research_gap_requires_a_cited_evidence_chain():
    source = paper("p1")
    valid = "[inferred] Paper IDs: p1. Evidence: The abstract reports a simulated evaluation of federated learning in hospitals. Limitation: no clinical validation is described. Unresolved question: does this generalize to hospitals? Proposed gap: test multi-site clinical deployment."
    assert _is_traceable_gap(valid, [source])
    assert not _is_traceable_gap("Real-world evidence is limited.", [source])


def test_theme_ids_are_deduplicated_and_exact_repeated_findings_consolidated():
    source = paper("p1")
    finding = source.abstract
    synthesis = Synthesis(themes=[
        Theme(id="a", title="First", description="", paper_ids=["p1", "p1", "unknown"], key_findings=[finding]),
        Theme(id="b", title="Second", description="", paper_ids=["p1"], key_findings=[finding]),
    ])

    result = SynthesisAgent._attach_evidence_matrix(synthesis, [source])

    assert result.themes[0].paper_ids == ["p1"]
    assert len(result.themes) == 1
    assert result.themes[0].key_findings == ["[p1] " + finding]
    assert result.evidence_matrix[0].themes == ["a"]
    assert result.evidence_matrix[0].included_in_synthesis is True


def test_abstract_evidence_gets_theme_links_but_metadata_only_paper_is_not_counted():
    clinical = Paper(
        id="clinical-eeg",
        title="Secure aggregation for clinical EEG",
        year=2024,
        source="arxiv",
        abstract="Clinical EEG data from hospitals uses masking-based secure aggregation. Evaluation reports model accuracy and communication overhead.",
    )
    metadata_only = Paper(id="metadata-only", title="Federated health privacy", year=2023, source="crossref", abstract=None)
    output = Synthesis(
        paper_analyses=[PaperAnalysis(
            paper_id="metadata-only", title=metadata_only.title, research_problem="unknown",
            methodology="unknown", dataset=None, key_findings=[], contribution="unknown",
            limitations=[], relevance="unknown",
        )],
        evidence_matrix=[PaperEvidence(
            paper_id=clinical.id, title=clinical.title,
            evidence_text="Clinical EEG data from hospitals uses masking-based secure aggregation.",
        )],
    )

    result = SynthesisAgent._attach_evidence_matrix(output, [clinical, metadata_only])
    clinical_row = next(row for row in result.evidence_matrix if row.paper_id == clinical.id)
    metadata_row = next(row for row in result.evidence_matrix if row.paper_id == metadata_only.id)

    assert clinical_row.included_in_synthesis is True
    assert clinical_row.privacy_mechanism == "secure aggregation, masking"
    assert clinical_row.healthcare_relevance.startswith("Direct")
    assert clinical_row.themes
    assert metadata_row.included_in_synthesis is False
    assert metadata_row.evidence_level == "metadata_only"
    assert result.paper_analyses == []


class CaptureProvider(AcademicSource):
    def __init__(self):
        super().__init__(name="capture")
        self.received_years = None

    async def search(self, query, limit=10, start_year=None, end_year=None, **kwargs):
        self.received_years = (start_year, end_year)
        return [paper("historical-retrieval", year=1899)]


@pytest.mark.asyncio
async def test_retrieval_does_not_send_year_bounds_to_providers():
    provider = CaptureProvider()
    retriever = MultiProviderRetriever(providers=[provider], cache_enabled=False)
    plan = SearchPlan(
        research_question="historical methods",
        search_queries=["historical method"],
        preferred_sources=["capture"],
        min_publication_year=2019,
        date_range=DateRange(start_year=2019, end_year=2025),
    )

    records = await retriever.retrieve_for_plan(plan)

    assert provider.received_years == (None, None)
    assert records[0].year == 1899


@pytest.mark.asyncio
async def test_synthesis_keeps_old_and_undated_papers():
    agent = SynthesisAgent(BrokenProvider())
    result = await agent.synthesize("Question", [paper("old", year=2018), paper("unknown-year", year=None)])

    assert {row.paper_id for row in result.evidence_matrix} == {"old", "unknown-year"}
    assert result.themes
    assert any("Only 2 papers" in warning for warning in result.quality_warnings)
