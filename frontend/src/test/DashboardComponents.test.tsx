import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { DashboardHeader } from '../components/DashboardHeader';
import { AgentTimeline } from '../components/AgentTimeline';
import { ThemeSynthesis } from '../components/ThemeSynthesis';
import { ReflectionView } from '../components/ReflectionView';
import { EvaluationView } from '../components/EvaluationView';
import { HistoryDrawer } from '../components/HistoryDrawer';
import { Navbar } from '../components/Navbar';
import { ResearchRun, AgentEvent, Theme, EvaluationData } from '../types';

const sampleRun: ResearchRun = {
  id: 'run-abc-123456',
  research_question: 'How does RAG improve factuality?',
  status: 'running',
  created_at: '2026-10-24T10:00:00Z',
  updated_at: '2026-10-24T10:01:00Z',
  current_iteration: 1,
  max_iterations: 3,
  coverage: 0.65,
  total_papers: 8,
  relevant_papers_count: 7,
  themes_count: 2,
  iterations_count: 1,
};

describe('Dashboard & Trace Components', () => {
  it('renders Navbar and triggers New Review and History callbacks', () => {
    const onNew = vi.fn();
    const onHist = vi.fn();
    render(<Navbar onNewResearch={onNew} onOpenHistory={onHist} isMockMode={true} />);

    expect(screen.getByText(/Mock Mode \(Offline\)/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText(/History/i));
    expect(onHist).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByText(/New Review/i));
    expect(onNew).toHaveBeenCalledTimes(1);
  });

  it('renders DashboardHeader and allows cancelling running loop', () => {
    const onCancel = vi.fn();
    render(<DashboardHeader run={sampleRun} onCancel={onCancel} />);

    expect(screen.getByText(/How does RAG improve factuality\?/i)).toBeInTheDocument();
    expect(screen.getByText('65%')).toBeInTheDocument();

    const cancelBtn = screen.getByText(/Cancel Run/i);
    fireEvent.click(cancelBtn);
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('renders AgentTimeline and expands event payload on click', () => {
    const events: AgentEvent[] = [
      {
        id: 'evt-1',
        run_id: 'run-1',
        event_type: 'planner.completed',
        iteration: 1,
        message: 'Generated 5 search queries.',
        timestamp: '2026-10-24T10:00:05Z',
        payload: { query_count: 5 },
      },
    ];

    render(<AgentTimeline events={events} />);
    expect(screen.getByText('Generated 5 search queries.')).toBeInTheDocument();
    expect(screen.queryByText(/Event Payload Metadata/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByText('Generated 5 search queries.'));
    expect(screen.getByText(/Event Payload Metadata/i)).toBeInTheDocument();
    expect(screen.getByText(/"query_count": 5/i)).toBeInTheDocument();
  });

  it('renders ThemeSynthesis and toggles theme expansion', () => {
    const themes: Theme[] = [
      {
        id: 't-1',
        theme_id: 'theme-1',
        title: 'Non-Parametric Grounding',
        description: 'Vector index retrieval.',
        paper_ids: ['p1', 'p2'],
        key_findings: ['Lowers hallucinations by 32%'],
        contradictions_or_tensions: ['Latency vs precision tension'],
      },
    ];

    render(
      <ThemeSynthesis
        themes={themes}
        synthesis={{
          agreements: ['Consensus on precision'],
          contradictions: ['Reranking debate'],
          trends: ['Agentic loops'],
        }}
      />
    );

    expect(screen.getByText('Non-Parametric Grounding')).toBeInTheDocument();
    expect(screen.getByText('Lowers hallucinations by 32%')).toBeInTheDocument();
    expect(screen.getByText('Consensus on precision')).toBeInTheDocument();
  });

  it('renders ReflectionView with missing topics and recommended queries', () => {
    render(
      <ReflectionView
        reflection={{
          coverage_score: 0.65,
          relevance_score: 0.88,
          missing_topics: ['RGB Benchmark', 'FactScore'],
          weak_areas: ['Hybrid sparse-dense comparison'],
          contradictions: [],
          outdated_areas: [],
          recommended_queries: ['RAG RGB benchmark evaluation'],
          should_replan: true,
          reason: 'Missing standardized benchmarks.',
        }}
      />
    );

    expect(screen.getByText('65%')).toBeInTheDocument();
    expect(screen.getByText('RGB Benchmark')).toBeInTheDocument();
    expect(screen.getByText(/RAG RGB benchmark evaluation/i)).toBeInTheDocument();
  });

  it('renders EvaluationView with benchmark comparison metrics', () => {
    const evalData: EvaluationData = {
      run_id: 'run-1',
      coverage: 0.9,
      relevance: 0.89,
      coherence: 1.0,
      citation_distribution: {
        total_citations: 9855,
        mean_citations: 1407.86,
      },
      evaluation_type: 'benchmark',
      benchmark_comparison: {
        paper_recall: 1.0,
        found_key_papers: ['Lewis et al. 2020'],
        missed_key_papers: [],
        topic_overlap_score: 1.0,
        covered_topics: ['Grounding'],
        missed_topics: [],
        finding_alignment_score: 1.0,
        summary: 'Benchmark Comparison: 100% recall.',
      },
    };

    render(<EvaluationView evaluation={evalData} />);
    expect(screen.getByText('Ground-Truth Benchmark Validated')).toBeInTheDocument();
    expect(screen.getByText('9,855')).toBeInTheDocument();
    expect(screen.getByText(/Lewis et al\. 2020/i)).toBeInTheDocument();
  });

  it('renders HistoryDrawer and selects a past run', () => {
    const onSelect = vi.fn();
    const onClose = vi.fn();

    render(
      <HistoryDrawer
        isOpen={true}
        onClose={onClose}
        runs={[sampleRun]}
        activeRunId="run-abc-123456"
        onSelectRun={onSelect}
      />
    );

    expect(screen.getByText(/Past Research Reviews/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText(/How does RAG improve factuality\?/i));
    expect(onSelect).toHaveBeenCalledWith('run-abc-123456');
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
