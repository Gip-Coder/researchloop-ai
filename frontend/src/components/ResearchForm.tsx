import React, { useState } from 'react';
import { ArrowRight, SlidersHorizontal, Sparkles } from 'lucide-react';
import { ResearchConfigInput } from '../types';

interface ResearchFormProps {
  onSubmit: (question: string, config: ResearchConfigInput) => void;
  isLoading: boolean;
}

const EXAMPLE_QUESTIONS = [
  'What are current methods for factuality evaluation in retrieval-augmented generation?',
  'How do self-reflective critic agents improve multi-hop question answering in LLMs?',
  'What are empirical trade-offs between dense passage retrieval and BM25 hybrid ranking?',
];

export const ResearchForm: React.FC<ResearchFormProps> = ({ onSubmit, isLoading }) => {
  const [question, setQuestion] = useState('');
  const [showConfig, setShowConfig] = useState(false);
  const [maxIterations, setMaxIterations] = useState(3);
  const [targetCoverage, setTargetCoverage] = useState(0.85);
  const [mockMode, setMockMode] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;
    onSubmit(question.trim(), {
      max_iterations: Number(maxIterations),
      target_coverage: Number(targetCoverage),
      mock_mode: mockMode,
      llm_provider: mockMode ? 'mock' : 'openai',
    });
  };

  return (
    <section className="hero-section">
      <h1 className="hero-title">Autonomous Literature Review</h1>
      <p className="hero-subtitle">
        Deploy an autonomous agent pipeline with iterative planning, multi-source retrieval,
        cross-paper thematic synthesis, and self-reflective gap analysis.
      </p>

      <form onSubmit={handleSubmit} className="input-card">
        <textarea
          className="question-textarea"
          rows={3}
          aria-label="Research Question"
          placeholder="What would you like to research? (e.g. What are current methods for factuality evaluation in RAG?)"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={isLoading}
        />

        {showConfig && (
          <div className="config-panel">
            <div className="config-item">
              <label htmlFor="max-iterations-input" className="config-label">Max Iterations (Loops)</label>
              <input
                id="max-iterations-input"
                type="number"
                min={1}
                max={5}
                className="config-input"
                value={maxIterations}
                onChange={(e) => setMaxIterations(Number(e.target.value))}
                disabled={isLoading}
              />
            </div>

            <div className="config-item">
              <label htmlFor="target-coverage-input" className="config-label">Target Coverage Threshold</label>
              <input
                id="target-coverage-input"
                type="number"
                step="0.05"
                min={0.5}
                max={1.0}
                className="config-input"
                value={targetCoverage}
                onChange={(e) => setTargetCoverage(Number(e.target.value))}
                disabled={isLoading}
              />
            </div>

            <div className="config-item">
              <label htmlFor="research-mode-select" className="config-label">Research Mode</label>
              <select
                id="research-mode-select"
                className="config-select"
                value={mockMode ? 'mock' : 'live'}
                onChange={(e) => setMockMode(e.target.value === 'mock')}
                disabled={isLoading}
              >
                <option value="mock">Mock Mode (Deterministic & Offline)</option>
                <option value="live">Live Mode (Real APIs)</option>
              </select>
            </div>
          </div>
        )}

        <div className="input-controls">
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => setShowConfig(!showConfig)}
          >
            <SlidersHorizontal size={14} />
            <span>{showConfig ? 'Hide Config' : 'Configure Parameters'}</span>
          </button>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={!question.trim() || isLoading}
          >
            {isLoading ? (
              <span>Initializing Loop...</span>
            ) : (
              <>
                <Sparkles size={16} />
                <span>Start Autonomous Review</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </div>
      </form>

      <div className="examples-container">
        <span className="examples-label">Try example:</span>
        {EXAMPLE_QUESTIONS.map((q, idx) => (
          <button
            key={idx}
            type="button"
            className="example-chip"
            onClick={() => setQuestion(q)}
          >
            {q}
          </button>
        ))}
      </div>
    </section>
  );
};
