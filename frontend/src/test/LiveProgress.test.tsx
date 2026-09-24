import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { LiveProgress } from '../components/LiveProgress';
import { AgentEvent } from '../types';

const sampleEvents: AgentEvent[] = [
  {
    id: 'e1',
    run_id: 'r1',
    event_type: 'research.started',
    iteration: 0,
    message: 'Research loop initialized for RAG inquiry',
    timestamp: '2026-09-24T12:00:00Z',
    payload: {},
  },
  {
    id: 'e2',
    run_id: 'r1',
    event_type: 'reflection.completed',
    iteration: 1,
    message: 'Critic evaluated coverage at 65%',
    timestamp: '2026-09-24T12:01:00Z',
    payload: {
      coverage_score: 0.65,
      missing_topics: ['Evaluation benchmarks (RGB, FactScore)'],
    },
  },
];

describe('LiveProgress Component', () => {
  it('renders progress messages and research gaps', () => {
    render(<LiveProgress events={sampleEvents} isRunning={false} />);
    expect(screen.getByText(/Research loop initialized for RAG inquiry/i)).toBeInTheDocument();
    expect(screen.getByText(/Critic evaluated coverage at 65%/i)).toBeInTheDocument();
    expect(screen.getByText(/Evaluation benchmarks \(RGB, FactScore\)/i)).toBeInTheDocument();
  });
});
