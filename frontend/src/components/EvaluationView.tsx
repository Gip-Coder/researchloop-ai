import React from 'react';
import { Award, BarChart3, CheckCircle, FileCheck, Layers, Target } from 'lucide-react';
import { EvaluationData } from '../types';

interface EvaluationViewProps {
  evaluation?: EvaluationData;
}

export const EvaluationView: React.FC<EvaluationViewProps> = ({ evaluation }) => {
  if (!evaluation) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        Evaluation metrics will be calculated after completion of the research loop.
      </div>
    );
  }

  const covPct = Math.round((evaluation.coverage || 0) * 100);
  const relPct = Math.round((evaluation.relevance || 0) * 100);
  const cohPct = Math.round((evaluation.coherence || 0) * 100);
  const citationStats = evaluation.citation_distribution || {};

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 600 }}>System & Literature Evaluation</h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Empirical quality metrics measuring scientific coverage, retriever precision,
            and thematic coherence.
          </p>
        </div>

        <span
          className="brand-badge"
          style={{
            backgroundColor: evaluation.evaluation_type === 'benchmark' ? 'var(--purple-bg)' : '#f1f5f9',
            color: evaluation.evaluation_type === 'benchmark' ? 'var(--purple)' : 'var(--text-secondary)',
            border: `1px solid ${evaluation.evaluation_type === 'benchmark' ? 'var(--purple-border)' : 'var(--border-subtle)'}`,
            fontSize: '0.775rem',
            padding: '0.25rem 0.75rem',
          }}
        >
          {evaluation.evaluation_type === 'benchmark'
            ? 'Ground-Truth Benchmark Validated'
            : 'Intrinsic Agent Evaluation'}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="paper-card" style={{ textAlign: 'center' }}>
          <div className="metric-title">Coverage Score</div>
          <div className="metric-value" style={{ color: covPct >= 85 ? 'var(--success)' : 'var(--primary)' }}>
            {covPct}%
          </div>
          <div className="metric-desc">Sub-question breadth</div>
        </div>

        <div className="paper-card" style={{ textAlign: 'center' }}>
          <div className="metric-title">Relevance Precision</div>
          <div className="metric-value" style={{ color: 'var(--primary)' }}>
            {relPct}%
          </div>
          <div className="metric-desc">Mean relevance across corpus</div>
        </div>

        <div className="paper-card" style={{ textAlign: 'center' }}>
          <div className="metric-title">Synthesis Coherence</div>
          <div className="metric-value" style={{ color: 'var(--purple)' }}>
            {cohPct}%
          </div>
          <div className="metric-desc">Grounding, balance & depth</div>
        </div>

        <div className="paper-card" style={{ textAlign: 'center' }}>
          <div className="metric-title">Total Citations</div>
          <div className="metric-value">
            {citationStats.total_citations?.toLocaleString() ?? '—'}
          </div>
          <div className="metric-desc">
            Mean: {citationStats.mean_citations ? Math.round(citationStats.mean_citations) : '—'}
          </div>
        </div>
      </div>

      {evaluation.benchmark_comparison ? (
        <div className="paper-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <Award size={18} style={{ color: 'var(--purple)' }} />
            <h4 style={{ fontSize: '1rem', fontWeight: 600 }}>
              Curated Benchmark Comparison (Ground Truth Review)
            </h4>
          </div>

          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
            {evaluation.benchmark_comparison.summary}
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
            <div style={{ background: '#f8fafc', padding: '0.875rem', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                Key Paper Recall ({Math.round(evaluation.benchmark_comparison.paper_recall * 100)}%)
              </div>
              <ul style={{ paddingLeft: '1.25rem', marginTop: '0.5rem', fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                {evaluation.benchmark_comparison.found_key_papers.map((p, i) => (
                  <li key={i} style={{ color: 'var(--success)' }}>
                    ✓ {p}
                  </li>
                ))}
                {evaluation.benchmark_comparison.missed_key_papers.map((p, i) => (
                  <li key={i} style={{ color: 'var(--danger)' }}>
                    ✗ {p}
                  </li>
                ))}
              </ul>
            </div>

            <div style={{ background: '#f8fafc', padding: '0.875rem', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                Topic Overlap ({Math.round(evaluation.benchmark_comparison.topic_overlap_score * 100)}%)
              </div>
              <ul style={{ paddingLeft: '1.25rem', marginTop: '0.5rem', fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                {evaluation.benchmark_comparison.covered_topics.map((t, i) => (
                  <li key={i} style={{ color: 'var(--success)' }}>
                    ✓ {t}
                  </li>
                ))}
                {evaluation.benchmark_comparison.missed_topics.map((t, i) => (
                  <li key={i} style={{ color: 'var(--warning)' }}>
                    ⚠ {t}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      ) : (
        <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          <strong>Note on Benchmark Evaluation:</strong> This inquiry was scored using intrinsic
          grounding heuristics. When a human-curated survey exists for the research question in the
          system benchmark registry, comparative recall and topic alignment are automatically populated.
        </div>
      )}
    </div>
  );
};
