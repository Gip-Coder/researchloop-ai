import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ResearchForm } from '../components/ResearchForm';

describe('ResearchForm Component', () => {
  it('renders research input and start button', () => {
    const onSubmit = vi.fn();
    render(<ResearchForm onSubmit={onSubmit} isLoading={false} />);

    expect(screen.getByPlaceholderText(/What would you like to research/i)).toBeInTheDocument();
    expect(screen.getByText(/Start Autonomous Review/i)).toBeInTheDocument();
  });

  it('allows clicking example questions', () => {
    const onSubmit = vi.fn();
    render(<ResearchForm onSubmit={onSubmit} isLoading={false} />);

    const exampleChip = screen.getByText(/What are current methods for factuality evaluation/i);
    fireEvent.click(exampleChip);

    const textarea = screen.getByPlaceholderText(/What would you like to research/i) as HTMLTextAreaElement;
    expect(textarea.value).toContain('factuality evaluation');
  });

  it('submits research question with config', () => {
    const onSubmit = vi.fn();
    render(<ResearchForm onSubmit={onSubmit} isLoading={false} isMockMode={true} />);

    const textarea = screen.getByPlaceholderText(/What would you like to research/i);
    fireEvent.change(textarea, { target: { value: 'How does RAG reduce hallucinations?' } });

    const submitBtn = screen.getByText(/Start Autonomous Review/i);
    fireEvent.click(submitBtn);

    expect(onSubmit).toHaveBeenCalledWith(
      'How does RAG reduce hallucinations?',
      expect.objectContaining({
        max_iterations: 3,
        target_coverage: 0.85,
        mock_mode: true,
      })
    );
  });
});
