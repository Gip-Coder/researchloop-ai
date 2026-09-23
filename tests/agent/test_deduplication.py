"""
Tests for Deduplicator.
"""

from __future__ import annotations

import pytest
from backend.agent.filtering.deduplication import Deduplicator
from backend.agent.models.paper import Paper


def test_deduplicate_exact_doi():
    dedup = Deduplicator()
    p1 = Paper(
        id="p1",
        title="Attention Is All You Need",
        authors=["Vaswani et al."],
        doi="10.5555/3295222.3295349",
        source="arxiv",
        citation_count=50000
    )
    p2 = Paper(
        id="p2",
        title="Attention is all you need: A study",
        authors=["A. Vaswani"],
        doi="https://doi.org/10.5555/3295222.3295349",
        source="semantic_scholar",
        citation_count=51000
    )

    result = dedup.deduplicate([p1, p2])
    assert len(result) == 1
    assert result[0].citation_count == 51000
    assert result[0].doi == "10.5555/3295222.3295349"


def test_deduplicate_normalized_title():
    dedup = Deduplicator()
    p1 = Paper(
        id="p1",
        title="BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        authors=["Jacob Devlin", "Ming-Wei Chang"],
        source="arxiv"
    )
    p2 = Paper(
        id="p2",
        title="BERT Pre training of Deep Bidirectional Transformers for Language Understanding!",
        authors=["J. Devlin"],
        source="crossref"
    )

    result = dedup.deduplicate([p1, p2])
    assert len(result) == 1
    assert len(result[0].authors) == 2


def test_deduplicate_fuzzy_title_matching():
    dedup = Deduplicator(fuzzy_threshold=0.90)
    p1 = Paper(
        id="p1",
        title="Dense Passage Retrieval for Open Domain Question Answering",
        authors=["Vladimir Karpukhin", "Barlas Oguz"],
        year=2020,
        source="arxiv"
    )
    p2 = Paper(
        id="p2",
        title="Dense Passage Retrieval for Open-Domain Question Answering System",
        authors=["V. Karpukhin"],
        year=2020,
        source="semantic_scholar"
    )

    result = dedup.deduplicate([p1, p2])
    assert len(result) == 1


def test_deduplicate_preserves_distinct_papers():
    dedup = Deduplicator()
    p1 = Paper(
        id="p1",
        title="Language Models are Few-Shot Learners",
        authors=["Tom Brown et al."],
        year=2020,
        source="arxiv"
    )
    p2 = Paper(
        id="p2",
        title="Language Models are Zero-Shot Reasoners",
        authors=["Takeshi Kojima et al."],
        year=2022,
        source="arxiv"
    )

    result = dedup.deduplicate([p1, p2])
    assert len(result) == 2


def test_metadata_merging_prefers_richest():
    dedup = Deduplicator()
    p1 = Paper(
        id="p1",
        title="Deep Residual Learning for Image Recognition",
        authors=["Kaiming He"],
        abstract=None,
        year=None,
        doi=None,
        citation_count=10000,
        source="arxiv"
    )
    p2 = Paper(
        id="p2",
        title="Deep Residual Learning for Image Recognition",
        authors=["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
        abstract="Deeper neural networks are more difficult to train. We present a residual learning framework.",
        year=2016,
        doi="10.1109/CVPR.2016.90",
        citation_count=180000,
        url="https://doi.org/10.1109/CVPR.2016.90",
        venue="CVPR",
        source="crossref"
    )

    result = dedup.deduplicate([p1, p2])
    assert len(result) == 1
    m = result[0]
    assert m.abstract is not None
    assert m.year == 2016
    assert m.doi == "10.1109/CVPR.2016.90"
    assert m.citation_count == 180000
    assert len(m.authors) == 4
    assert m.venue == "CVPR"

