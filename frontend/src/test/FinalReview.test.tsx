import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { FinalReview } from '../components/FinalReview';
import { ResearchResultData, Paper } from '../types';

const sampleResult: ResearchResultData = {
  run_id: 'run-123',
  research_question: 'How does RAG improve factuality?',
  status: 'completed',
  coverage_score: 0.90,
  stop_reason: 'target_coverage_reached',
  final_review: {
    title: 'Literature Review: Factuality in Retrieval-Augmented Generation',
    narrative: 'Retrieval-Augmented Generation decomposes factual access into non-parametric memory and parametric generation.',
    key_themes: [
      {
        title: 'Non-Parametric Memory Grounding',
        description: 'Coupling vector indexes with neural generation.',
        paper_count: 3,
        key_findings: ['Reduces factual drift by 32%'],
      },
    ],
    consensus_findings: ['Retriever precision is paramount'],
    open_research_gaps: ['Conflicting evidence resolution in multi-document settings'],
    coherence_score: 1.0,
    relevance_score: 0.92,
  },
  metadata: {},
};

const samplePapers: Paper[] = [
  {
    id: 'p1',
    title: 'Retrieval-Augmented Generation for NLP Tasks',
    authors: ['Patrick Lewis'],
    year: 2020,
    source: 'arxiv',
    citation_count: 5000,
    is_relevant: true,
    categories: ['cs.CL'],
  },
];

describe('FinalReview Component', () => {
  it('renders literature review title, narrative, themes, and bibliography', () => {
    render(<FinalReview result={sampleResult} papers={samplePapers} />);
    expect(screen.getByText(/Literature Review: Factuality in Retrieval-Augmented Generation/i)).toBeInTheDocument();
    expect(screen.getByText(/Retrieval-Augmented Generation decomposes factual access/i)).toBeInTheDocument();
    expect(screen.getByText(/Non-Parametric Memory Grounding/i)).toBeInTheDocument();
    expect(screen.getByText(/Retriever precision is paramount/i)).toBeInTheDocument();
    expect(screen.getByText(/Conflicting evidence resolution in multi-document settings/i)).toBeInTheDocument();
    expect(screen.getByText(/Patrick Lewis/i)).toBeInTheDocument();
  });
});
