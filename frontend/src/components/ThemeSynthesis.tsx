import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Layers, Check, AlertCircle, ArrowUpRight } from 'lucide-react';
import { ResearchResultData, Theme } from '../types';

interface ThemeSynthesisProps {
  themes: Theme[];
  synthesis?: ResearchResultData['synthesis'];
}

export const ThemeSynthesis: React.FC<ThemeSynthesisProps> = ({ themes, synthesis }) => {
  const [expandedThemeId, setExpandedThemeId] = useState<string | null>(
    themes.length > 0 ? themes[0].theme_id : null
  );

  const toggleTheme = (id: string) => {
    setExpandedThemeId(expandedThemeId === id ? null : id);
  };

  return (
    <div>
      <h3 style={{ fontSize: '1.15rem', fontWeight: 600, marginBottom: '0.5rem' }}>
        Emergent Thematic Clusters
      </h3>
      <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
        Synthesized thematic structures dynamically extracted by clustering literature across
        methodologies, problem formulations, and findings.
      </p>

      {themes.length === 0 ? (
        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          Themes will appear once the synthesis stage completes.
        </div>
      ) : (
        themes.map((theme) => {
          const isExpanded = expandedThemeId === theme.theme_id;

          return (
            <div key={theme.id || theme.theme_id} className="theme-card">
              <div className="theme-header" onClick={() => toggleTheme(theme.theme_id)}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div
                    style={{
                      width: 28,
                      height: 28,
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: 'var(--primary-subtle)',
                      color: 'var(--primary)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Layers size={16} />
                  </div>
                  <div>
                    <h4 className="theme-title">{theme.title}</h4>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {theme.paper_ids.length} supporting papers
                    </span>
                  </div>
                </div>

                <button className="btn btn-outline btn-sm">
                  {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>
              </div>

              {isExpanded && (
                <div className="theme-body">
                  <p style={{ fontSize: '0.925rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '1rem' }}>
                    {theme.description}
                  </p>

                  <div style={{ marginBottom: '1rem' }}>
                    <div style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.4rem' }}>
                      Key Consolidated Findings:
                    </div>
                    <ul style={{ paddingLeft: '1.25rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                      {theme.key_findings.map((f, i) => (
                        <li key={i} style={{ marginBottom: '0.35rem' }}>
                          {f}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {theme.contradictions_or_tensions?.length > 0 && (
                    <div
                      style={{
                        padding: '0.75rem',
                        backgroundColor: 'var(--warning-bg)',
                        border: '1px solid var(--warning-border)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.825rem',
                        color: '#92400e',
                        marginBottom: '1rem',
                      }}
                    >
                      <strong>Contradictions or Tensions:</strong>
                      <ul style={{ paddingLeft: '1.25rem', marginTop: '0.25rem' }}>
                        {theme.contradictions_or_tensions.map((c, i) => (
                          <li key={i}>{c}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                      Referenced Paper IDs:
                    </span>
                    {theme.paper_ids.map((pid) => (
                      <span
                        key={pid}
                        style={{
                          fontSize: '0.75rem',
                          fontFamily: 'var(--font-mono)',
                          padding: '0.15rem 0.45rem',
                          backgroundColor: '#f1f5f9',
                          borderRadius: '4px',
                        }}
                      >
                        {pid}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })
      )}

      {synthesis && (
        <div style={{ marginTop: '2.5rem' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 600, marginBottom: '1rem' }}>
            Cross-Paper Comparative Analysis
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
            {synthesis.agreements && synthesis.agreements.length > 0 && (
              <div
                style={{
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1.25rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <Check size={16} style={{ color: 'var(--success)' }} />
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Scientific Consensus</h4>
                </div>
                <ul style={{ paddingLeft: '1.25rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {synthesis.agreements.map((a, i) => (
                    <li key={i} style={{ marginBottom: '0.4rem' }}>{a}</li>
                  ))}
                </ul>
              </div>
            )}

            {synthesis.contradictions && synthesis.contradictions.length > 0 && (
              <div
                style={{
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1.25rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <AlertCircle size={16} style={{ color: 'var(--danger)' }} />
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Tensions & Contradictions</h4>
                </div>
                <ul style={{ paddingLeft: '1.25rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {synthesis.contradictions.map((c, i) => (
                    <li key={i} style={{ marginBottom: '0.4rem' }}>{c}</li>
                  ))}
                </ul>
              </div>
            )}

            {synthesis.trends && synthesis.trends.length > 0 && (
              <div
                style={{
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1.25rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <ArrowUpRight size={16} style={{ color: 'var(--primary)' }} />
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Emerging Research Trends</h4>
                </div>
                <ul style={{ paddingLeft: '1.25rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {synthesis.trends.map((t, i) => (
                    <li key={i} style={{ marginBottom: '0.4rem' }}>{t}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
