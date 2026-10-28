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
        "doi": "10.48550/arXiv.2005.11401",
        "url": "https://arxiv.org/abs/2005.11401",
        "source": "arxiv",
        "citation_count": 4820,
        "citation_count_available": True,
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
        "source": "arxiv",
        "citation_count": 3150,
        "citation_count_available": True,
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
        "citation_count_available": True,
        "categories": ["cs.CL", "cs.AI"]
    },
    {
        "id": "mock-chen-2024-rgb",
        "title": "Benchmarking Large Language Models in Retrieval-Augmented Generation",
        "authors": ["Jiawei Chen", "Hongyu Lin", "Xianpei Han", "Le Sun"],
        "abstract": "Retrieval-Augmented Generation (RAG) is prone to noise sensitivity and factual degradation under conflicting passages. We construct the RGB benchmark evaluating 4 essential abilities: noise robustness, negative rejection, information integration, and counterfactual robustness.",
        "year": 2024,
        "venue": "AAAI",
        "doi": "10.1609/aaai.v38i16.29728",
        "url": "https://arxiv.org/abs/2309.01431",
        "source": "arxiv",
        "citation_count": 14,
        "citation_count_available": True,
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
        "source": "crossref",
        "citation_count": 12,
        "citation_count_available": True,
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
        "citation_count": 11,
        "citation_count_available": True,
        "categories": ["cs.CL", "cs.IR"]
    },
    {
        "id": "mock-cuconasu-2024-noise",
        "title": "The Power of Noise: Redefining Retrieval for RAG Systems",
        "authors": ["Florin Cuconasu", "Giovanni Trappolini", "Federico Siciliano", "Simone Filice", "Cesare Campagnano", "Yoelle Maarek", "Nicola Tonellotto", "Fabrizio Silvestri"],
        "abstract": "We analyze how retrieved document quality affects RAG generation. Counter-intuitively, inserting even distractor documents with related keywords can sometimes improve reasoning, but completely off-topic noise causes catastrophic hallucinations.",
        "year": 2024,
        "venue": "SIGIR",
        "doi": "10.1145/3626772.3657834",
        "url": "https://arxiv.org/abs/2401.14887",
        "source": "arxiv",
        "citation_count": 10,
        "citation_count_available": True,
        "categories": ["cs.IR", "cs.CL"]
    },
    {
        "id": "mock-shuster-2021-retrieval",
        "title": "Retrieval Augmentation Reduces Hallucination in Conversation",
        "authors": ["Kurt Shuster", "Spencer Poff", "Moya Chen", "Douwe Kiela", "Jason Weston"],
        "abstract": "We demonstrate that conversational neural agents hallucinate substantially less when grounded in retrieved passages from large external corpora, comparing neural reader-generator variants across multi-turn knowledge dialogues.",
        "year": 2021,
        "venue": "EMNLP findings",
        "doi": "10.18653/v1/2021.findings-emnlp.320",
        "url": "https://arxiv.org/abs/2104.07567",
        "source": "arxiv",
        "citation_count": 15,
        "citation_count_available": True,
        "categories": ["cs.CL", "cs.AI"]
    },
    {
        "id": "mock-borgeaud-2022-retro",
        "title": "Improving Language Models by Retrieving from Trillions of Tokens",
        "authors": ["Sebastian Borgeaud", "Arthur Mensch", "Jordan Hoffmann", "Trevor Cai", "Eliza Rutherford", "Katie Millican", "George van den Driessche"],
        "abstract": "We present RETRO (Retrieval-Enhanced Transformer), an autoregressive language model equipped with retrieval over trillions of tokens, showing that retrieval allows 7B parameter models to compete with 280B parameter dense models on factual perplexity.",
        "year": 2022,
        "venue": "ICML",
        "doi": "10.48550/arXiv.2112.04426",
        "url": "https://arxiv.org/abs/2112.04426",
        "source": "crossref",
        "citation_count": 850,
        "citation_count_available": True,
        "categories": ["cs.CL", "cs.LG"]
    },
    {
        "id": "mock-guu-2020-realm",
        "title": "REALM: Retrieval-Augmented Language Model Pre-Training",
        "authors": ["Kelvin Guu", "Kenton Lee", "Zora Tung", "Panupong Pasupat", "Ming-Wei Chang"],
        "abstract": "Language model pre-training imparts general knowledge, but models struggle with precise factual recall. We introduce REALM, augmenting pre-training with a learned neural retriever trained end-to-end via masked language modeling.",
        "year": 2020,
        "venue": "ICML",
        "doi": "10.48550/arXiv.2002.08909",
        "url": "https://arxiv.org/abs/2002.08909",
        "source": "crossref",
        "citation_count": 1890,
        "citation_count_available": True,
        "categories": ["cs.CL", "cs.AI"]
    },
    {
        "id": "mock-ram-2023-in-context-ralm",
        "title": "In-Context Retrieval-Augmented Language Models",
        "authors": ["Ori Ram", "Yoav Levine", "Roi Levin", "Amir Globerson"],
        "abstract": "We investigate simple in-context retrieval-augmented language models without modifying LM parameters, demonstrating substantial LM perplexity and open-domain factual accuracy improvements across diverse corpora.",
        "year": 2023,
        "venue": "TACL",
        "doi": "10.1162/tacl_a_00605",
        "url": "https://arxiv.org/abs/2302.00083",
        "source": "arxiv",
        "citation_count": None,
        "citation_count_available": False,
        "categories": ["cs.CL", "cs.AI"]
    },
    {
        "id": "mock-vaswani-2017-attention",
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit", "Llion Jones", "Aidan N. Gomez", "Lukasz Kaiser", "Illia Polosukhin"],
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose the Transformer, based entirely on attention mechanisms.",
        "year": 2017,
        "venue": "NeurIPS",
        "doi": "10.48550/arXiv.1706.03762",
        "url": "https://arxiv.org/abs/1706.03762",
        "source": "arxiv",
        "citation_count": 95000,
        "citation_count_available": True,
        "categories": ["cs.CL", "cs.LG"]
    },
    {
        "id": "mock-distractor-quantum-algae",
        "title": "Quantum Biology and Photosynthetic Energy Transfer in Cryptophyte Algae",
        "authors": ["Gregory D. Scholes", "Elisabet Romero", "Rohan S. Henderson"],
        "abstract": "Coherence in biological photosynthesis demonstrates persistent quantum phenomena at physiological temperatures, affecting excitation energy transfer across antenna complexes.",
        "year": 2022,
        "venue": "Nature Chemistry",
        "doi": "10.1038/nature05678",
        "url": "https://doi.org/10.1038/nature05678",
        "source": "crossref",
        "citation_count": 95,
        "citation_count_available": True,
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
            eligible = [p for p in self.corpus if not (start_year and p.year and p.year < start_year)]
            results = [p.model_copy(deep=True) for p in eligible[:2]]

        return results
