"""
Synthesis Agent for deep per-paper and cross-paper literature synthesis.
"""

from __future__ import annotations

import logging
import re
from backend.agent.models.paper import Paper
from backend.agent.models.synthesis import Synthesis, Theme, PaperEvidence
from backend.agent.prompts.synthesis import SYNTHESIS_SYSTEM_PROMPT, build_synthesis_prompt
from backend.providers.llm.base import LLMProvider

logger = logging.getLogger(__name__)

_QUANTIFIED_CLAIM = re.compile(
    r"\b\d+(?:\.\d+)?\s*%|\b\d+(?:\.\d+)?\s*(?:percentage points?|ms|milliseconds?|seconds?|minutes?|hours?|GB|MB)\b|"
    r"\b(?:accuracy|AUC|F1|precision|recall|overhead|latency|performance)\D{0,20}\b\d+(?:\.\d+)?\b",
    re.IGNORECASE,
)


def _has_source_for_quantities(claim: str, papers: list[Paper]) -> bool:
    """Reject numeric performance claims unless their quantities occur in supplied source text."""
    if not _QUANTIFIED_CLAIM.search(claim):
        return True
    source_text = " ".join(f"{paper.year or ''} {paper.abstract or ''}" for paper in papers)
    quantities = re.findall(r"\d+(?:\.\d+)?\s*%?", claim)
    return all(quantity.strip() in source_text for quantity in quantities)


def _has_cited_paper(claim: str, papers: list[Paper]) -> bool:
    return any(paper.id and paper.id in claim for paper in papers)


def _is_traceable_gap(gap: str, papers: list[Paper]) -> bool:
    required = ("paper ids:", "evidence:", "limitation:", "unresolved question:", "proposed gap:")
    lowered = gap.casefold()
    structure_ok = (
        any(tag in lowered for tag in ("[author-acknowledged]", "[inferred]", "[search-needed]"))
        and all(part in lowered for part in required)
        and _has_cited_paper(gap, papers)
    )
    if not structure_ok:
        return False
    evidence_match = re.search(r"evidence:\s*(.*?)\s*limitation:", gap, re.I | re.S)
    if not evidence_match:
        return False
    evidence = evidence_match.group(1).strip().strip('"` ')
    cited_sources = [paper for paper in papers if paper.id in gap]
    return bool(evidence) and any(paper.abstract and evidence in paper.abstract for paper in cited_sources)


class SynthesisAgent:
    """Agent responsible for detailed extraction, thematic clustering, and comparative synthesis."""

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def synthesize(
        self,
        research_question: str,
        relevant_papers: list[Paper],
        min_publication_year: int | None = None,
    ) -> Synthesis:
        """
        Produce comprehensive literature synthesis from relevant papers.
        Extracts per-paper analyses, groups into dynamic themes, and extracts cross-paper insights.
        """
        # Year is metadata only. Keep the compatibility argument, but do not filter on it.
        eligible_papers = list(relevant_papers)
        if not eligible_papers:
            return Synthesis(
                paper_analyses=[],
                themes=[],
                agreements=[],
                differences=[],
                contradictions=[],
                methodological_differences=[],
                trends=[],
                research_gaps=[],
                narrative_summary="No relevant papers were available for synthesis.",
                quality_warnings=["No relevant evidence was available; no substantive findings or research gaps were generated."]
            )

        # Prioritize top scored relevant papers for high-fidelity synthesis within context limits
        sorted_papers = sorted(
            eligible_papers,
            key=lambda p: (p.relevance_score is not None, p.relevance_score or 0.0),
            reverse=True
        )[:10]

        prompt = build_synthesis_prompt(
            research_question=research_question,
            relevant_papers=sorted_papers
        )

        try:
            synthesis = await self.llm.generate_structured(
                prompt=prompt,
                response_model=Synthesis,
                system_prompt=SYNTHESIS_SYSTEM_PROMPT,
                max_retries=2
            )
            return self._attach_evidence_matrix(synthesis, sorted_papers)

        except Exception as err:
            logger.error(f"[SynthesisAgent] Synthesis generation failed: {err}. Building fallback synthesis.")
            return self._build_fallback_synthesis(research_question, sorted_papers)

    @staticmethod
    def _attach_evidence_matrix(synthesis: Synthesis, papers: list[Paper]) -> Synthesis:
        """Attach evidence only when it points to source text; metadata alone is not a contribution."""
        paper_by_id = {paper.id: paper for paper in papers}
        source_matrix = {row.paper_id: row for row in synthesis.evidence_matrix}
        rejected_quantities = False

        def retain_supported(items: list[str]) -> list[str]:
            nonlocal rejected_quantities
            kept = [item for item in items if _has_source_for_quantities(item, papers)]
            rejected_quantities |= len(kept) != len(items)
            return kept

        # Keep per-paper analyses only when the model supplied an exact source passage.
        analyses = []
        for analysis in synthesis.paper_analyses:
            paper = paper_by_id.get(analysis.paper_id)
            if not paper or not paper.abstract:
                continue
            passages = [quote for quote in analysis.supporting_evidence if quote and quote in paper.abstract]
            if not passages:
                continue
            analysis.title = paper.title
            analysis.source_url = paper.url or (f"https://doi.org/{paper.doi}" if paper.doi else None)
            analysis.evidence_level = "abstract_only"
            analysis.supporting_evidence = passages
            analysis.key_findings = [finding for finding in analysis.key_findings if finding and finding in paper.abstract]
            analysis.limitations = retain_supported(analysis.limitations)
            analyses.append(analysis)
        synthesis.paper_analyses = analyses

        # Validate model-created themes against source excerpts and valid paper IDs.
        valid_themes: list[Theme] = []
        for theme in synthesis.themes:
            backed_findings: list[str] = []
            backed_ids: set[str] = set()
            for finding in retain_supported(theme.key_findings):
                cited = [pid for pid in theme.paper_ids if pid in paper_by_id and paper_by_id[pid].abstract and finding in paper_by_id[pid].abstract]
                if cited:
                    pid = cited[0]
                    backed_ids.add(pid)
                    backed_findings.append(f"[{pid}] {finding}")
            if backed_findings:
                theme.paper_ids = sorted(backed_ids)
                theme.key_findings = list(dict.fromkeys(backed_findings))
                theme.description = "Source excerpts from the listed papers; abstract-level evidence only."
                valid_themes.append(theme)

        # If the model omitted usable theme assignments, group literal abstract
        # excerpts by topics named in the text. This is an evidence index, not a
        # claim that the studies reached the same conclusion.
        if not valid_themes:
            topic_rules = [
                ("Privacy-preserving mechanisms", r"differential privacy|secure aggregation|secure multi.?party|homomorphic encryption|functional encryption|secret sharing|masking|encryption"),
                ("Privacy-accuracy-efficiency trade-offs", r"accuracy|performance|non.?iid|heterogeneity|overhead|communication|computation|latency"),
                ("Security threats and defenses", r"poison|inference attack|model inversion|membership inference|malicious|byzantine|tamper|gradient"),
                ("Healthcare deployment", r"healthcare|clinical|hospital|medical|patient|eeg|health system"),
                ("Evaluation quality", r"dataset|benchmark|experiment|evaluation|simulat|clinical reports|client configuration"),
            ]
            fallback_themes: list[Theme] = []
            for index, (title, pattern) in enumerate(topic_rules, start=1):
                ids: list[str] = []
                findings: list[str] = []
                for paper in papers:
                    if not paper.abstract or not re.search(pattern, paper.abstract, re.I):
                        continue
                    sentence = next(
                        (part.strip() for part in re.split(r"(?<=[.!?])\s+", paper.abstract) if re.search(pattern, part, re.I)),
                        paper.abstract.strip(),
                    )
                    ids.append(paper.id)
                    findings.append(f"[{paper.id}] {sentence}")
                if ids:
                    fallback_themes.append(Theme(
                        id=f"evidence-theme-{index}",
                        title=title,
                        description="Abstract excerpts grouped by terms present in the source text; this grouping does not establish cross-study agreement.",
                        paper_ids=ids,
                        key_findings=findings,
                    ))
            valid_themes = fallback_themes
            if valid_themes:
                synthesis.quality_warnings.append("Theme assignments were rebuilt from source excerpts because generated theme paper links were empty or unsupported.")
            present_titles = {theme.title for theme in valid_themes}
            missing_titles = [title for title, _ in topic_rules if title not in present_titles]
            if missing_titles:
                synthesis.quality_warnings.append("No source-backed abstract evidence was found for: " + ", ".join(missing_titles) + ".")

        seen_findings: set[str] = set()
        duplicate_removed = False
        for theme in valid_themes:
            unique_findings = []
            for finding in theme.key_findings:
                normalized = " ".join(finding.casefold().split())
                if normalized in seen_findings:
                    duplicate_removed = True
                    continue
                seen_findings.add(normalized)
                unique_findings.append(finding)
            theme.key_findings = unique_findings
            cited_ids = {
                match.group(1)
                for finding in unique_findings
                if (match := re.match(r"\[([^\]]+)\]\s+", finding))
            }
            theme.paper_ids = [pid for pid in theme.paper_ids if pid in cited_ids]
        valid_themes = [theme for theme in valid_themes if theme.paper_ids and theme.key_findings]
        if duplicate_removed:
            synthesis.quality_warnings.append("Exact duplicate findings across themes were consolidated.")
        synthesis.themes = valid_themes

        # Only source-backed paper analyses or theme excerpts count as used.
        used_ids = {analysis.paper_id for analysis in analyses}
        used_ids.update(pid for theme in valid_themes for pid in theme.paper_ids)
        synthesis.agreements = retain_supported(synthesis.agreements)
        synthesis.differences = retain_supported(synthesis.differences)
        synthesis.contradictions = retain_supported(synthesis.contradictions)
        synthesis.methodological_differences = retain_supported(synthesis.methodological_differences)
        synthesis.trends = retain_supported(synthesis.trends)
        comparative_fields = (synthesis.agreements, synthesis.differences, synthesis.contradictions, synthesis.methodological_differences, synthesis.trends)
        if any(len(claims) != len([claim for claim in claims if _has_cited_paper(claim, papers)]) for claims in comparative_fields):
            synthesis.quality_warnings.append("Comparative claims without a valid paper ID were removed.")
        for claims in comparative_fields:
            claims[:] = [claim for claim in claims if _has_cited_paper(claim, papers)]
        traceable_gaps = [gap for gap in synthesis.research_gaps if _is_traceable_gap(gap, papers)]
        if len(traceable_gaps) != len(synthesis.research_gaps):
            synthesis.quality_warnings.append("Untraceable research gaps were removed; each retained gap must name papers and show the evidence-to-limitation-to-question chain.")
        synthesis.research_gaps = retain_supported(traceable_gaps)
        if rejected_quantities:
            synthesis.quality_warnings.append("Unsupported quantitative claims were removed because the quantities were absent from supplied abstracts.")

        topic_by_id = {pid: [theme.id for theme in valid_themes if pid in theme.paper_ids] for pid in paper_by_id}
        matrix: list[PaperEvidence] = []
        for paper in papers:
            proposed = source_matrix.get(paper.id)
            verified_excerpt = bool(proposed and paper.abstract and proposed.evidence_text and proposed.evidence_text in paper.abstract)
            row = proposed.model_copy(deep=True) if verified_excerpt else PaperEvidence(paper_id=paper.id, title=paper.title)
            abstract = paper.abstract or ""
            mechanisms = [term for term in ("differential privacy", "secure aggregation", "secure multi-party computation", "homomorphic encryption", "functional encryption", "secret sharing", "masking") if re.search(re.escape(term), abstract, re.I)]
            sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", abstract) if part.strip()]
            healthcare = bool(re.search(r"healthcare|clinical|hospital|medical|patient|eeg|health system", abstract, re.I))
            iot_only = bool(re.search(r"internet of things|\biot\b", abstract, re.I)) and not healthcare
            accuracy_evidence = next((s for s in sentences if re.search(r"accuracy|auc|f1|performance|overhead|latency|non.?iid|heterogeneity", s, re.I)), None)
            security_evidence = next((s for s in sentences if re.search(r"poison|inference attack|malicious|byzantine|tamper|gradient|leak", s, re.I)), None)
            deployment_evidence = next((s for s in sentences if re.search(r"healthcare|clinical|hospital|medical|patient|institution|silo|iot", s, re.I)), None)
            dataset_evidence = next((s for s in sentences if re.search(r"dataset|benchmark|experiment|evaluation|simulat|framework|protocol", s, re.I)), None)
            limitation_evidence = [s for s in sentences if re.search(r"however|limitation|challenge|overhead|remain|although|introduce additional", s, re.I)]
            row.paper_id = paper.id
            row.title = paper.title
            row.year = paper.year
            row.source_url = paper.url or (f"https://doi.org/{paper.doi}" if paper.doi else None)
            row.healthcare_relevance = ("Direct healthcare context is stated in the abstract." if healthcare else "IoT context is present, but healthcare relevance is not established in the abstract." if iot_only else None)
            row.privacy_mechanism = ", ".join(mechanisms) if mechanisms else None
            row.accuracy_evaluation = accuracy_evidence
            row.security_threat_or_defense = security_evidence
            row.deployment_context = deployment_evidence
            row.dataset_and_method = dataset_evidence
            row.main_supported_finding = sentences[0] if sentences else None
            row.author_reported_limitations = limitation_evidence
            row.themes = topic_by_id.get(paper.id, [])
            row.included_in_synthesis = paper.id in used_ids
            row.evidence_level = "abstract_only" if paper.abstract else "metadata_only"
            row.evidence_text = paper.abstract
            matrix.append(row)
        synthesis.evidence_matrix = matrix

        if len(used_ids) < 6:
            synthesis.quality_warnings.append(f"Only {len(used_ids)} papers contributed source-backed evidence; the preferred range is 6-10.")
        if any(not paper.abstract for paper in papers):
            synthesis.quality_warnings.append("Some eligible records had metadata only; they were not counted as substantive synthesis contributions.")
        if not synthesis.narrative_summary or not any(_has_cited_paper(sentence, papers) for sentence in re.split(r"(?<=[.!?])\s+", synthesis.narrative_summary)):
            source_ids = ", ".join(f"[{pid}]" for pid in sorted(used_ids))
            synthesis.narrative_summary = (
                f"The available abstract-level evidence was organized into {len(valid_themes)} themes across {len(used_ids)} contributing papers {source_ids}. "
                "These excerpts support topic mapping, but do not establish full-text quality, comparative effect sizes, or field-wide conclusions."
                if used_ids else "No papers with source-backed substantive evidence contributed to the synthesis. See the evidence matrix for the eligible records and missing information."
            )
            synthesis.quality_warnings.append("The generated executive summary lacked traceable paper IDs and was replaced with a scope-limited summary.")
        return synthesis

    def _build_fallback_synthesis(
        self,
        research_question: str,
        papers: list[Paper]
    ) -> Synthesis:
        # A generation failure is not evidence. Keep the source matrix for audit,
        # but do not fabricate findings, datasets, consensus, or research gaps.
        return self._attach_evidence_matrix(Synthesis(
            research_gaps=[],
            narrative_summary="Automated synthesis could not be generated. Retrieved metadata and abstracts are retained in the evidence matrix for manual review.",
            quality_warnings=["Synthesis generation failed; no substantive claims were produced."],
        ), papers)

