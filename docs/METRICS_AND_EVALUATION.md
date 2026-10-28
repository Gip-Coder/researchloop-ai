# METRICS AND EVALUATION DOCUMENTATION

**Project:** ResearchLoop AI — Agentic AI Pipeline for Autonomous Literature Review  
**Author:** Independent QA and AI Research Engineering Audit  
**Date:** 2026-10-28  

---

## 1. Overview & Purpose

This document provides mathematical definitions, evaluation rubrics, data sources, denominators, and critical limitations for all qualitative and quantitative evaluation metrics computed within ResearchLoop AI.

---

## 2. Metric Specifications

### A. Coverage Score (`coverage_score`)

1. **Definition:** Evaluates the degree to which essential conceptual facets, sub-questions, and literature dimensions of the research question are addressed in the reviewed corpus.
2. **Formula / Scoring Rubric:**
   - **Primary (LLM Critic Evaluation):** Computed by the `CriticAgent` using a structured assessment prompt evaluating:
     - Dimension completeness across planned sub-questions.
     - Presence of empirical benchmark data.
     - Representation of failure modes and noise sensitivity.
     - *Scale:* $0.0 \le \text{Score} \le 1.0$ (percentage representation in UI).
   - **Heuristic Fallback:** When LLM reflection is disabled or fails:
     $$\text{Coverage}_{\text{heuristic}} = \min\left(1.0, \frac{|\text{Relevant Papers}|}{\max(1, |\text{Sub-Questions}|)} \times 0.25\right)$$
3. **Data Source:** `ResearchState.relevant_papers`, `ResearchState.search_plan`, and `ResearchState.synthesis`.
4. **Limitations & Disclosures:**
   - In offline mock mode (`MockLLMProvider`), coverage progresses from 0.65 in Iteration 1 to 0.90 in Iteration 2 as a deterministic simulation of gap closure.
   - It is a **qualitative heuristic proxy** representing model-judged completeness. It is **not** an objective percentage of human knowledge or an absolute proof of completeness.

---

### B. Relevance Precision (`relevance_score`)

1. **Definition:** The proportion of retrieved and evaluated academic candidate papers that meet the specific inclusion criteria of the research plan.
2. **Formula:**
   $$\text{Relevance} = \frac{\sum_{p \in \mathcal{P}} \text{relevance\_score}(p)}{|\mathcal{P}|}$$
   Where $\mathcal{P}$ is the set of candidate papers retaining an evaluated relevance score. If individual continuous scores are absent, defaults to binary ratio $\frac{|\{p \in \mathcal{P} : p.\text{is\_relevant} = \text{True}\}|}{|\mathcal{P}|}$.
3. **Data Source:** Per-paper structured evaluations from `RelevanceFilter` (`RelevanceDecision.relevance_score`).
4. **Limitations:**
   - Pre-filtering checks publication year against the search plan's date range; papers outside the range receive a score of $0.10$ and are marked non-relevant.

---

### C. Synthesis Coherence (`coherence_score`)

1. **Definition:** A composite metric evaluating structural grounding, thematic balance, nuance, and narrative completeness in the generated literature review.
2. **Formula:**
   $$\text{Coherence} = 0.25 \cdot S_{\text{grounding}} + 0.25 \cdot S_{\text{depth}} + 0.25 \cdot S_{\text{nuance}} + 0.25 \cdot S_{\text{narrative}}$$
   - **Theme Grounding ($S_{\text{grounding}}$):** Ratio of theme-referenced paper IDs that have corresponding structured extractions in `paper_analyses`.
   - **Substantive Depth ($S_{\text{depth}}$):** Ratio of themes supported by $\ge 1$ paper and $\ge 1$ concrete key finding.
   - **Dialectical Nuance ($S_{\text{nuance}}$):** Evaluates presence of (1) consensus agreements, (2) differing viewpoints, and (3) contradictions/methodological tensions ($1/3$ point each).
   - **Narrative Completeness ($S_{\text{narrative}}$):** $1.0$ if actionable research gaps and an executive narrative ($\ge 50$ chars) exist; $0.5$ if only one exists; $0.0$ otherwise.
3. **Limitations:**
   - A score of 100% indicates that all four structural and dialectical criteria are satisfied. It does **not** signify that the scientific claims are universally true, only that the synthesis is structurally rigorous and grounded.

---

### D. Benchmark Comparison (`benchmark_comparison`)

1. **Definition:** Automated evaluation comparing the agent's synthesized output against a curated gold-standard survey stored in `tests/fixtures/curated_review.json`.
2. **Constituent Metrics:**
   - **Paper Recall:** Proportion of gold-standard key papers retrieved by the agent:
     $$\text{Recall}_{\text{paper}} = \frac{|\mathcal{P}_{\text{found}}|}{|\mathcal{P}_{\text{benchmark}}|}$$
   - **Topic Overlap:** Proportion of expected survey topics covered by emergent theme descriptions:
     $$\text{Overlap}_{\text{topic}} = \frac{|\mathcal{T}_{\text{covered}}|}{|\mathcal{T}_{\text{benchmark}}|}$$
   - **Finding Alignment:** Proportion of ground-truth findings mirrored in the narrative summary or theme findings.
3. **Limitations:**
   - Only active when a curated survey matching the topic exists in the benchmark registry. For unindexed research questions, the system defaults to intrinsic evaluation.

---

## 3. Stopping Conditions Policy

The engine terminates its autonomous feedback loop upon the earliest of:
1. `target_coverage_reached`: Assessed coverage score meets or exceeds `config.target_coverage`.
2. `diminishing_returns_no_new_papers`: An iteration yields fewer than `config.min_new_relevant_papers` new relevant papers.
3. `stagnant_repeated_gaps`: The critic identifies the exact same missing topics as the previous iteration with zero new evidence acquired.
4. `critic_satisfied_coverage`: The critic explicitly marks `should_replan = False`.
5. `max_iterations_reached`: Total loop cycles reach `config.max_iterations`.
