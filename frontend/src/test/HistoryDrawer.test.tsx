import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { HistoryDrawer } from '../components/HistoryDrawer';
import { ResearchRun } from '../types';

const sampleRuns: ResearchRun[] = [
  {
    id: 'run-1',
    research_question: 'How does self-rag improve citations?',
    status: 'completed',
    created_at: '2026-10-29T00:30:00Z',
    updated_at: '2026-10-29T00:32:00Z',
    current_iteration: 2,
    max_iterations: 3,
    iterations_count: 2,
    total_papers: 8,
    relevant_papers_count: 7,
    themes_count: 3,
    coverage: 0.85,
  },
  {
    id: 'run-2',
    research_question: 'What are graph neural network scaling limits?',
    status: 'failed',
    created_at: '2026-10-28T15:00:00Z',
    updated_at: '2026-10-28T15:01:00Z',
    current_iteration: 1,
    max_iterations: 3,
    iterations_count: 1,
    total_papers: 3,
    relevant_papers_count: 1,
    themes_count: 0,
    coverage: 0.40,
  },
];

describe('HistoryDrawer Component', () => {
  it('renders history runs when open', () => {
    render(
      <HistoryDrawer
        isOpen={true}
        onClose={vi.fn()}
        runs={sampleRuns}
        activeRunId={undefined}
        onSelectRun={vi.fn()}
        onDeleteRun={vi.fn()}
        onClearAll={vi.fn()}
      />
    );

    expect(screen.getByText(/How does self-rag improve citations\?/i)).toBeInTheDocument();
    expect(screen.getByText(/What are graph neural network scaling limits\?/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Clear all research history/i })).toBeInTheDocument();
  });

  it('triggers onDeleteRun after two-click inline confirmation', async () => {
    const onDeleteRun = vi.fn().mockResolvedValue(undefined);
    render(
      <HistoryDrawer
        isOpen={true}
        onClose={vi.fn()}
        runs={sampleRuns}
        activeRunId={undefined}
        onSelectRun={vi.fn()}
        onDeleteRun={onDeleteRun}
        onClearAll={vi.fn()}
      />
    );

    const deleteButtons = screen.getAllByRole('button', { name: /Delete research history entry/i });
    expect(deleteButtons.length).toBe(2);

    // Click delete on first run
    fireEvent.click(deleteButtons[0]);

    // Should now show Delete this run? and Confirm delete button
    expect(screen.getByText(/Delete this run\?/i)).toBeInTheDocument();
    const confirmButton = screen.getByRole('button', { name: /Confirm delete/i });
    
    await act(async () => {
      fireEvent.click(confirmButton);
    });

    expect(onDeleteRun).toHaveBeenCalledWith('run-1');
  });

  it('cancels deletion when clicking Cancel', () => {
    const onDeleteRun = vi.fn();
    render(
      <HistoryDrawer
        isOpen={true}
        onClose={vi.fn()}
        runs={sampleRuns}
        activeRunId={undefined}
        onSelectRun={vi.fn()}
        onDeleteRun={onDeleteRun}
        onClearAll={vi.fn()}
      />
    );

    const deleteButtons = screen.getAllByRole('button', { name: /Delete research history entry/i });
    fireEvent.click(deleteButtons[0]);

    expect(screen.getByText(/Delete this run\?/i)).toBeInTheDocument();
    const cancelButton = screen.getByRole('button', { name: /Cancel delete/i });
    fireEvent.click(cancelButton);

    expect(screen.queryByText(/Delete this run\?/i)).not.toBeInTheDocument();
    expect(onDeleteRun).not.toHaveBeenCalled();
  });

  it('triggers onClearAll after confirmation', async () => {
    const onClearAll = vi.fn().mockResolvedValue(undefined);
    render(
      <HistoryDrawer
        isOpen={true}
        onClose={vi.fn()}
        runs={sampleRuns}
        activeRunId={undefined}
        onSelectRun={vi.fn()}
        onDeleteRun={vi.fn()}
        onClearAll={onClearAll}
      />
    );

    const clearAllButton = screen.getByRole('button', { name: /Clear all research history/i });
    fireEvent.click(clearAllButton);

    expect(screen.getByText(/Clear all research runs\?/i)).toBeInTheDocument();
    const confirmClearBtn = screen.getByRole('button', { name: /Yes, delete all/i });

    await act(async () => {
      fireEvent.click(confirmClearBtn);
    });

    expect(onClearAll).toHaveBeenCalled();
  });
});
