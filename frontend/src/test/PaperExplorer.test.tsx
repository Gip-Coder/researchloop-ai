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
    citation_count: 4800,
    is_relevant: true,
    relevance_score: 0.95,
    relevance_reason: 'Seminal RAG paper',
    categories: ['cs.CL'],
  },
  {
    id: 'p2',
    title: 'Benchmarking Large Language Models in Retrieval-Augmented Generation',
    authors: ['Jiawei Chen', 'Hongyin Zhu'],
    year: 2024,
    source: 'semantic_scholar',
    citation_count: 320,
    is_relevant: true,
    relevance_score: 0.88,
    relevance_reason: 'RAG factuality benchmark RGB',
    categories: ['cs.AI'],
  },
  {
    id: 'p3',
    title: 'Irrelevant Study on Protein Folding',
    authors: ['Other Author'],
    year: 2021,
    source: 'crossref',
    citation_count: 50,
    is_relevant: false,
    relevance_score: 0.12,
    relevance_reason: 'Off-topic domain',
    categories: ['bio'],
  },
];

describe('PaperExplorer Component', () => {
  it('renders all papers initially', () => {
    render(<PaperExplorer papers={samplePapers} />);
    expect(screen.getByText(/Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks/i)).toBeInTheDocument();
    expect(screen.getByText(/Benchmarking Large Language Models/i)).toBeInTheDocument();
    expect(screen.getByText(/Irrelevant Study on Protein Folding/i)).toBeInTheDocument();
  });

  it('filters papers by search keyword', () => {
    render(<PaperExplorer papers={samplePapers} />);
    const searchInput = screen.getByPlaceholderText(/Search papers by keyword/i);

    fireEvent.change(searchInput, { target: { value: 'Benchmarking' } });

    expect(screen.getByText(/Benchmarking Large Language Models/i)).toBeInTheDocument();
    expect(screen.queryByText(/Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks/i)).not.toBeInTheDocument();
  });

  it('filters by relevance status', () => {
    render(<PaperExplorer papers={samplePapers} />);
    const selects = screen.getAllByRole('combobox');
    const relevanceSelect = selects[1]; // second select is relevance

    fireEvent.change(relevanceSelect, { target: { value: 'relevant' } });

    expect(screen.getByText(/Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks/i)).toBeInTheDocument();
    expect(screen.queryByText(/Irrelevant Study on Protein Folding/i)).not.toBeInTheDocument();
  });
});
