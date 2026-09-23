"""
Deterministic Mock Academic Provider delivering high-fidelity realistic papers.
"""

from __future__ import annotations

import re
from typing import Any
from backend.agent.retrieval.base import AcademicSource
from backend.agent.models.paper import Paper

MOCK_CORPUS: list[dict[str, Any]] = [
    {
        "id": "mock-lewis-2020-rag",
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "authors": ["Patrick Lewis", "Ethan Perez", "Aleksandra Piktus", "Fabio Petroni", "Vladimir Karpukhin", "Sebastian Riedel", "Douwe Kiela"],
        "abstract": "Large pre-trained language models store factual knowledge in their parameters, but their ability to access and manipulate knowledge is limited on knowledge-intensive tasks. We build RAG models where parametric memory is combined with non-parametric (retrieved) passage index, dramatically reducing hallucinations.",
        "year": 2020,
        "venue": "NeurIPS",
        "doi": "10.5555/3495724.3496517",
        "url": "https://arxiv.org/abs/2005.11401",
        "source": "arxiv",
        "citation_count": 4820,
        "categories": ["cs.CL", "cs.AI"]
    },
    {
        "id": "mock-karpukhin-2020-dpr",
        "title": "Dense Passage Retrieval for Open-Domain Question Answering",
        "authors": ["Vladimir Karpukhin", "Barlas Oguz", "Sewon Min", "Patrick Lewis", "Ledell Wu", "Sergey Edunov", "Danqi Chen", "Wen-tau Yih"],
        "abstract": "Open-domain question answering relies on efficient passage retrieval to select candidate contexts. We show that retrieval can be practically implemented using dense representations learned from a dual-encoder architecture, outperforming traditional Lucene BM25.",
        "year": 2020,
        "venue": "EMNLP",
        "doi": "10.18653/v1/2020.emnlp-main.550",
        "url": "https://arxiv.org/abs/2004.04906",
        "source": "semantic_scholar",
        "citation_count": 3150,
        "categories": ["cs.CL", "cs.IR"]
    },
    {
        "id": "mock-min-2023-factscore",
        "title": "FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long-form Text Generation",
        "authors": ["Sewon Min", "Kalpesh Krishna", "Xinxi Lyu", "Mike Lewis", "Wen-tau Yih", "Pang Wei Koh", "Mohit Iyyer", "Luke Zettlemoyer", "Hannaneh Hajishirzi"],
        "abstract": "Evaluating factual accuracy in long-form generation is challenging. We introduce FActScore, breaking generation into atomic facts and measuring the percentage supported by verifiable knowledge sources, establishing rigorous empirical evaluation for RAG factuality.",
        "year": 2023,
        "venue": "EMNLP",
        "doi": "10.18653/v1/2023.emnlp-main.741",
        "url": "https://arxiv.org/abs/2305.14251",
        "source": "crossref",
        "citation_count": 410,
        "categories": ["cs.CL", "cs.AI"]
    },
    {
        "id": "mock-chen-2024-rgb",
        "title": "Benchmarking Large Language Models in Retrieval-Augmented Generation",
        "authors": ["Jiawei Chen", "Hongyu Lin", "Xianpei Han", "Le Sun"],
        "abstract": "Retrieval-Augmented Generation (RAG) is prone to noise sensitivity and factual degradation under conflicting passages. We construct the RGB benchmark evaluating 4 essential abilities: noise robustness, negative rejection, information integration, and counterfactual robustness.",
        "year": 2024,
        "venue": "AAAI",
        "doi": "10.1609/aaai.v38i16.29705",
        "url": "https://arxiv.org/abs/2309.01414",
        "source": "arxiv",
        "citation_count": 285,
        "categories": ["cs.CL", "cs.AI"]
    },
    {
        "id": "mock-asai-2024-selfrag",
        "title": "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection",
        "authors": ["Akari Asai", "Zeqiu Wu", "Yizhong Wang", "Avirup Sil", "Hannaneh Hajishirzi"],
        "abstract": "Despite the success of RAG, indiscriminate retrieval can introduce noise or irrelevant context. We introduce Self-RAG, an end-to-end framework where language models learn to dynamically retrieve on-demand and reflectively critique generated segments with special reflection tokens.",
        "year": 2024,
        "venue": "ICLR",
        "doi": "10.48550/arXiv.2310.11511",
        "url": "https://arxiv.org/abs/2310.11511",
        "source": "semantic_scholar",
        "citation_count": 620,
        "categories": ["cs.CL", "cs.AI"]
    },
    {
        "id": "mock-es-2024-ragas",
        "title": "Ragas: Automated Evaluation of Retrieval Augmented Generation",
        "authors": ["Shahul Es", "Jithin James", "Luis Espinosa-Anke", "Steven Schockaert"],
        "abstract": "Assessing RAG pipelines requires evaluating both retrieval quality and generator factuality. We present Ragas, an automated evaluation framework providing metrics for faithfulness, answer relevance, and context precision without relying on ground-truth human annotations.",
        "year": 2024,
        "venue": "EACL",
        "doi": "10.18653/v1/2024.eacl-demo.16",
        "url": "https://arxiv.org/abs/2309.15217",
        "source": "crossref",
        "citation_count": 390,
        "categories": ["cs.CL", "cs.IR"]
    },
    {
        "id": "mock-cuconasu-2024-noise",
        "title": "The Power of Noise: Redefining Retrieval for RAG Systems",
        "authors": ["Florin Cuconasu", "Giovanni Trappolini", "Federico Siciliano", "Simone Filice", "Cesare Campagnano", "Yoelle Maarek", "Nicola Tonellotto", "Fabrizio Silvestri"],
        "abstract": "We analyze how retrieved document quality affects RAG generation. Counter-intuitively, inserting even distractor documents with related keywords can sometimes improve reasoning, but completely off-topic noise causes catastrophic hallucinations.",
        "year": 2024,
        "venue": "SIGIR",
        "doi": "10.1145/3626772.3657835",
        "url": "https://arxiv.org/abs/2401.14887",
        "source": "semantic_scholar",
        "citation_count": 140,
        "categories": ["cs.IR", "cs.CL"]
    },
    {
        "id": "mock-distractor-quantum-algae",
        "title": "Quantum Biology and Photosynthetic Energy Transfer in Cryptophyte Algae",
        "authors": ["Gregory D. Scholes", "Elisabet Romero", "Rohan S. Henderson"],
        "abstract": "Coherence in biological photosynthesis demonstrates persistent quantum phenomena at physiological temperatures, affecting excitation energy transfer across antenna complexes.",
        "year": 2022,
        "venue": "Nature Chemistry",
        "doi": "10.1038/s41557-021-00812-7",
        "url": "https://doi.org/10.1038/s41557-021-00812-7",
        "source": "crossref",
        "citation_count": 95,
        "categories": ["physics.chem-ph", "q-bio.BM"]
    }
]


class MockAcademicProvider(AcademicSource):
    """Academic provider serving pre-indexed fixture papers for offline and testing runs."""

    def __init__(self, name: str = "mock_academic"):
        super().__init__(name=name)
        self.corpus = [Paper.model_validate(p) for p in MOCK_CORPUS]

    async def search(
        self,
        query: str,
        limit: int = 10,
        start_year: int | None = None,
        end_year: int | None = None,
        **kwargs: Any
    ) -> list[Paper]:
        query_words = set(re.findall(r"\w+", query.lower()))

        scored_papers = []
        for paper in self.corpus:
            # Check year bounds
            if start_year and paper.year and paper.year < start_year:
                continue
            if end_year and paper.year and paper.year > end_year:
                continue

            text = f"{paper.title} {paper.abstract or ''}".lower()
            overlap = sum(1 for w in query_words if w in text)
            if overlap > 0 or len(query_words) == 0:
                scored_papers.append((overlap, paper))

        # Sort by overlap score descending
        scored_papers.sort(key=lambda x: x[0], reverse=True)
        results = [p.model_copy(deep=True) for _, p in scored_papers[:limit]]

        # If empty match, return at least 2 default papers to simulate partial discovery
        if not results and self.corpus:
            results = [p.model_copy(deep=True) for p in self.corpus[:2]]

        return results
