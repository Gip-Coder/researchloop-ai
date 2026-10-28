import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { PaperExplorer } from '../components/PaperExplorer';
import { Paper } from '../types';

const samplePapers: Paper[] = [
  {
    id: 'p1',
    title: 'Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks',
    authors: ['Patrick Lewis', 'Ethan Perez'],
    year: 2020,
    source: 'arxiv',
    citation_count: 12,
    citation_count_available: true,
    is_relevant: true,
    relevance_score: 0.95,
    relevance_reason: 'Seminal RAG paper',
    categories: ['cs.CL'],
    matched_queries: ['"retrieval-augmented generation" evaluation'],
  },
  {
    id: 'p2',
    title: 'Benchmarking Large Language Models in Retrieval-Augmented Generation',
    authors: ['Jiawei Chen', 'Hongyin Zhu'],
    year: 2024,
    source: 'arxiv',
    citation_count: null,
    citation_count_available: false,
    is_relevant: true,
    relevance_score: 0.88,
    relevance_reason: 'RAG factuality benchmark RGB',
    categories: ['cs.AI'],
  },
  {
    id: 'p3',
    title: 'Foundational Information Retrieval Architecture',
    authors: ['Classic Author'],
    year: 2017,
    source: 'crossref',
    citation_count: 450,
    citation_count_available: true,
    is_relevant: true,
    relevance_score: 0.82,
    relevance_reason: 'Seminal pre-2019 architecture',
    is_foundational_exception: true,
    categories: ['cs.IR'],
  },
];

describe('PaperExplorer Component', () => {
  it('renders all papers initially', () => {
    render(<PaperExplorer papers={samplePapers} />);
    expect(screen.getByText(/Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks/i)).toBeInTheDocument();
    expect(screen.getByText(/Benchmarking Large Language Models/i)).toBeInTheDocument();
    expect(screen.getByText(/Foundational Information Retrieval Architecture/i)).toBeInTheDocument();
  });

  it('renders "Unavailable" when citation count is null or unavailable', () => {
    render(<PaperExplorer papers={samplePapers} />);
    expect(screen.getByText(/Unavailable/i)).toBeInTheDocument();
  });

  it('highlights papers in the preferred 10-15 citation range', () => {
    render(<PaperExplorer papers={samplePapers} />);
    expect(screen.getByText(/\(Preferred 10-15\)/i)).toBeInTheDocument();
  });

  it('displays foundational exception tag for pre-2019 papers', () => {
    render(<PaperExplorer papers={samplePapers} />);
    expect(screen.getByText(/Foundational Exception/i)).toBeInTheDocument();
  });

  it('displays matched search queries when present', () => {
    render(<PaperExplorer papers={samplePapers} />);
    expect(screen.getByText(/Retrieved by query:/i)).toBeInTheDocument();
    expect(screen.getByText(/"retrieval-augmented generation" evaluation/i)).toBeInTheDocument();
  });

  it('filters papers by search keyword', () => {
    render(<PaperExplorer papers={samplePapers} />);
    const searchInput = screen.getByPlaceholderText(/Search papers by keyword/i);

    fireEvent.change(searchInput, { target: { value: 'Benchmarking' } });

    expect(screen.getByText(/Benchmarking Large Language Models/i)).toBeInTheDocument();
    expect(screen.queryByText(/Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks/i)).not.toBeInTheDocument();
  });
});
