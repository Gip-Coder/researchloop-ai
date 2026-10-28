import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
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

  it('renders research stage tracker indicators', () => {
    render(<LiveProgress events={sampleEvents} isRunning={true} />);
    const stageBar = screen.getByLabelText('Research Stages');
    expect(within(stageBar).getByText('Planning')).toBeInTheDocument();
    expect(within(stageBar).getByText('Retrieval')).toBeInTheDocument();
    expect(within(stageBar).getByText('Thematic Synthesis')).toBeInTheDocument();
    expect(within(stageBar).getByText('Critic Evaluation')).toBeInTheDocument();
  });

  it('reveals resume follow pill when scrolled away and resumes on click', () => {
    const { container } = render(<LiveProgress events={sampleEvents} isRunning={true} />);

    // Find the scrollable container
    const scrollContainer = container.querySelector('div[style*="overflow-y: auto"], div[style*="overflowY: auto"]') ||
                            container.querySelectorAll('div')[2];
    expect(scrollContainer).toBeTruthy();

    // Simulate user scrolling up (scrollHeight 500, scrollTop 0, clientHeight 300 -> distance 200 > 60)
    Object.defineProperty(scrollContainer, 'scrollHeight', { value: 500, configurable: true, writable: true });
    Object.defineProperty(scrollContainer, 'clientHeight', { value: 300, configurable: true, writable: true });
    Object.defineProperty(scrollContainer, 'scrollTop', { value: 0, configurable: true, writable: true });

    fireEvent.scroll(scrollContainer);

    // Now the resume button "Follow latest" should appear
    const resumeBtn = screen.getByRole('button', { name: /Resume auto-scrolling to latest events/i });
    expect(resumeBtn).toBeInTheDocument();
    expect(screen.getByText(/Follow latest/i)).toBeInTheDocument();

    // Clicking resume re-enables auto-follow and hides the button
    fireEvent.click(resumeBtn);
    expect(screen.queryByRole('button', { name: /Resume auto-scrolling to latest events/i })).not.toBeInTheDocument();
  });
});
