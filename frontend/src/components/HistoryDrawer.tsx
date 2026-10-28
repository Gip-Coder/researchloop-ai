import React, { useState } from 'react';
import { X, CheckCircle, Clock, AlertCircle, Trash2, AlertTriangle, RefreshCw } from 'lucide-react';
import { ResearchRun } from '../types';

interface HistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  runs: ResearchRun[];
  activeRunId?: string;
  onSelectRun: (runId: string) => void;
  onDeleteRun?: (runId: string) => Promise<void>;
  onClearAll?: () => Promise<void>;
}

export const HistoryDrawer: React.FC<HistoryDrawerProps> = ({
  isOpen,
  onClose,
  runs,
  activeRunId,
  onSelectRun,
  onDeleteRun,
  onClearAll,
}) => {
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [isClearingAll, setIsClearingAll] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const formatRunDate = (isoStr: string) => {
    try {
      const d = new Date(isoStr);
      if (isNaN(d.getTime())) return 'Undated';
      return d.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return 'Undated';
    }
  };

  const handleDelete = async (e: React.MouseEvent, runId: string) => {
    e.stopPropagation();
    if (!onDeleteRun) return;
    setErrorMessage(null);
    setDeletingId(runId);
    try {
      await onDeleteRun(runId);
      setConfirmDeleteId(null);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to delete research entry.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleClearAll = async () => {
    if (!onClearAll) return;
    setErrorMessage(null);
    setIsClearingAll(true);
    try {
      await onClearAll();
      setShowClearConfirm(false);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to clear research history.');
    } finally {
      setIsClearingAll(false);
    }
  };

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>Past Research Reviews</h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {runs.length} {runs.length === 1 ? 'session' : 'sessions'} saved
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {runs.length > 0 && onClearAll && (
              <button
                className="btn btn-outline btn-sm"
                onClick={() => setShowClearConfirm(true)}
                title="Clear all history"
                aria-label="Clear all research history"
                style={{ color: 'var(--danger)', fontSize: '0.75rem', padding: '0.2rem 0.5rem' }}
              >
                Clear all
              </button>
            )}
            <button className="btn btn-outline btn-sm" onClick={onClose} aria-label="Close history drawer">
              <X size={16} />
            </button>
          </div>
        </div>

        {errorMessage && (
          <div
            style={{
              padding: '0.5rem 0.75rem',
              backgroundColor: 'var(--danger-bg)',
              borderBottom: '1px solid var(--danger-border)',
              color: 'var(--danger)',
              fontSize: '0.8rem',
            }}
          >
            {errorMessage}
          </div>
        )}

        {showClearConfirm && (
          <div
            style={{
              padding: '0.75rem',
              backgroundColor: '#fffbeb',
              borderBottom: '1px solid #fef3c7',
              fontSize: '0.825rem',
            }}
          >
            <div style={{ fontWeight: 600, color: '#92400e', marginBottom: '0.35rem' }}>
              Clear all research runs?
            </div>
            <div style={{ color: '#78350f', marginBottom: '0.5rem' }}>
              This will permanently delete all {runs.length} recorded research runs and their iterations.
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                className="btn btn-sm"
                style={{ backgroundColor: 'var(--danger)', color: '#fff', fontSize: '0.75rem', padding: '0.2rem 0.6rem' }}
                onClick={handleClearAll}
                disabled={isClearingAll}
              >
                {isClearingAll ? 'Clearing...' : 'Yes, delete all'}
              </button>
              <button
                className="btn btn-outline btn-sm"
                style={{ fontSize: '0.75rem', padding: '0.2rem 0.6rem' }}
                onClick={() => setShowClearConfirm(false)}
                disabled={isClearingAll}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        <div className="drawer-list">
          {runs.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No research runs recorded yet.
            </div>
          ) : (
            runs.map((r) => {
              const isActive = r.id === activeRunId;
              const covPct = Math.round((r.coverage || 0) * 100);
              const isDeleting = deletingId === r.id;
              const isConfirming = confirmDeleteId === r.id;

              return (
                <div
                  key={r.id}
                  className={`history-item ${isActive ? 'active' : ''}`}
                  onClick={() => {
                    if (!isConfirming) {
                      onSelectRun(r.id);
                      onClose();
                    }
                  }}
                  style={{ position: 'relative' }}
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
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {covPct}% coverage
                      </span>
                      {onDeleteRun && !isConfirming && (
                        <button
                          className="btn-icon"
                          aria-label="Delete research history entry"
                          title="Delete research history entry"
                          onClick={(e) => {
                            e.stopPropagation();
                            setConfirmDeleteId(r.id);
                          }}
                          style={{
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            color: 'var(--text-muted)',
                            padding: '2px',
                            display: 'flex',
                            alignItems: 'center',
                          }}
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
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
                    {formatRunDate(r.created_at)} • {r.total_papers} papers
                  </div>

                  {isConfirming && (
                    <div
                      onClick={(e) => e.stopPropagation()}
                      style={{
                        marginTop: '0.5rem',
                        padding: '0.5rem',
                        backgroundColor: '#fff1f2',
                        border: '1px solid #fecdd3',
                        borderRadius: 'var(--radius-sm)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: '0.5rem',
                      }}
                    >
                      <span style={{ fontSize: '0.75rem', color: '#be123c', fontWeight: 500 }}>
                        Delete this run?
                      </span>
                      <div style={{ display: 'flex', gap: '0.35rem' }}>
                        <button
                          className="btn btn-sm"
                          style={{
                            backgroundColor: 'var(--danger)',
                            color: '#fff',
                            fontSize: '0.7rem',
                            padding: '0.15rem 0.5rem',
                          }}
                          onClick={(e) => handleDelete(e, r.id)}
                          disabled={isDeleting}
                          aria-label="Confirm delete"
                        >
                          {isDeleting ? 'Deleting...' : 'Delete'}
                        </button>
                        <button
                          className="btn btn-outline btn-sm"
                          style={{ fontSize: '0.7rem', padding: '0.15rem 0.5rem' }}
                          onClick={(e) => {
                            e.stopPropagation();
                            setConfirmDeleteId(null);
                          }}
                          disabled={isDeleting}
                          aria-label="Cancel delete"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
