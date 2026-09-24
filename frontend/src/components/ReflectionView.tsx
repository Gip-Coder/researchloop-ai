import React from 'react';
import { AlertTriangle, CheckCircle, Lightbulb, Search, ShieldCheck } from 'lucide-react';
import { ResearchResultData } from '../types';

interface ReflectionViewProps {
  reflection?: ResearchResultData['reflection'];
}

export const ReflectionView: React.FC<ReflectionViewProps> = ({ reflection }) => {
  if (!reflection) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        Critic reflection will become available once the initial evaluation phase completes.
      </div>
    );
  }

  const covPct = Math.round(reflection.coverage_score * 100);
  const relPct = Math.round(reflection.relevance_score * 100);

  return (
    <div>
      <div className="reflection-summary-card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600 }}>Critic & Self-Reflection Audit</h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
              Self-correcting evaluation model assessing state-of-the-art coverage and literature gaps.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '1rem' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>COVERAGE</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: covPct >= 85 ? 'var(--success)' : 'var(--warning)' }}>
                {covPct}%
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>RELEVANCE</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--primary)' }}>
                {relPct}%
              </div>
            </div>
          </div>
        </div>

        <div
          style={{
            padding: '1rem',
            backgroundColor: '#f8fafc',
            borderLeft: '4px solid var(--primary)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.925rem',
            color: 'var(--text-primary)',
            marginBottom: '1.5rem',
          }}
        >
          <strong>Evaluation Rationale:</strong> {reflection.reason}
        </div>

        {/* Missing Topics / Research Gaps */}
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <AlertTriangle size={18} style={{ color: 'var(--warning)' }} />
            <h4 style={{ fontSize: '1rem', fontWeight: 600, color: '#92400e' }}>
              Critical Research Gaps & Missing Topics
            </h4>
          </div>

          {reflection.missing_topics.length === 0 ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--success)', fontSize: '0.9rem' }}>
              <CheckCircle size={16} />
              <span>No critical gaps detected. Literature coverage is exhaustive.</span>
            </div>
          ) : (
            <div>
              {reflection.missing_topics.map((gap, idx) => (
                <div key={idx} className="gap-pill">
                  <AlertTriangle size={14} />
                  <span>{gap}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recommended Queries */}
        {reflection.recommended_queries?.length > 0 && (
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <Search size={16} style={{ color: 'var(--primary)' }} />
              <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Recommended Iterative Search Queries</h4>
            </div>
            <ul style={{ paddingLeft: '1.25rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              {reflection.recommended_queries.map((q, idx) => (
                <li key={idx} style={{ marginBottom: '0.35rem', fontFamily: 'var(--font-mono)' }}>
                  "{q}"
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Weak Areas */}
        {reflection.weak_areas?.length > 0 && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <Lightbulb size={16} style={{ color: 'var(--text-muted)' }} />
              <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Under-Represented Sub-Dimensions</h4>
            </div>
            <ul style={{ paddingLeft: '1.25rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
              {reflection.weak_areas.map((w, idx) => (
                <li key={idx} style={{ marginBottom: '0.25rem' }}>{w}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};
