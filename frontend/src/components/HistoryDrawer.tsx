import React from 'react';
import { X, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { ResearchRun } from '../types';

interface HistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  runs: ResearchRun[];
  activeRunId?: string;
  onSelectRun: (runId: string) => void;
}

export const HistoryDrawer: React.FC<HistoryDrawerProps> = ({
  isOpen,
  onClose,
  runs,
  activeRunId,
  onSelectRun,
}) => {
  if (!isOpen) return null;

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Past Research Reviews</h3>
          <button className="btn btn-outline btn-sm" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="drawer-list">
          {runs.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No research runs recorded yet.
            </div>
          ) : (
            runs.map((r) => {
              const isActive = r.id === activeRunId;
              const covPct = Math.round((r.coverage || 0) * 100);

              return (
                <div
                  key={r.id}
                  className={`history-item ${isActive ? 'active' : ''}`}
                  onClick={() => {
                    onSelectRun(r.id);
                    onClose();
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                    <span
                      style={{
                        fontSize: '0.725rem',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        color: r.status === 'completed' ? 'var(--success)' : 'var(--text-muted)',
                      }}
                    >
                      {r.status}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {covPct}% coverage
                    </span>
                  </div>

                  <div
                    style={{
                      fontSize: '0.875rem',
                      fontWeight: 600,
                      color: 'var(--text-primary)',
                      lineHeight: 1.3,
                      marginBottom: '0.35rem',
                    }}
                  >
                    {r.research_question.length > 80
                      ? `${r.research_question.slice(0, 80)}...`
                      : r.research_question}
                  </div>

                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {new Date(r.created_at).toLocaleDateString()} • {r.total_papers} papers
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
