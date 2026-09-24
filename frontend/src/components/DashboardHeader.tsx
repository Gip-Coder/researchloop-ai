import React from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  FileText,
  Layers,
  StopCircle,
  TrendingUp,
} from 'lucide-react';
import { ResearchRun } from '../types';

interface DashboardHeaderProps {
  run: ResearchRun;
  onCancel?: () => void;
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({ run, onCancel }) => {
  const coveragePercent = Math.min(100, Math.round((run.coverage || 0) * 100));

  const getStatusBadge = () => {
    switch (run.status) {
      case 'completed':
        return (
          <span className="status-badge badge-completed">
            <CheckCircle2 size={13} />
            <span>Completed</span>
          </span>
        );
      case 'running':
        return (
          <span className="status-badge badge-running">
            <span
              style={{
                width: 7,
                height: 7,
                borderRadius: '50%',
                backgroundColor: '#2563eb',
                display: 'inline-block',
                animation: 'spin 1.5s infinite',
              }}
            />
            <span>Running Loop</span>
          </span>
        );
      case 'failed':
        return (
          <span className="status-badge badge-failed">
            <AlertCircle size={13} />
            <span>Failed</span>
          </span>
        );
      case 'cancelled':
        return (
          <span className="status-badge badge-cancelled">
            <StopCircle size={13} />
            <span>Cancelled</span>
          </span>
        );
      default:
        return (
          <span className="status-badge badge-pending">
            <Clock size={13} />
            <span>Pending</span>
          </span>
        );
    }
  };

  return (
    <div className="dashboard-header">
      <div className="dash-top">
        <div>
          <div className="dash-meta-pills">
            {getStatusBadge()}
            {run.stopping_reason && (
              <span className="brand-badge" style={{ textTransform: 'none' }}>
                Stop reason: {run.stopping_reason}
              </span>
            )}
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              ID: {run.id.slice(0, 8)}...
            </span>
          </div>
          <h2 className="dash-question" style={{ marginTop: '0.5rem' }}>
            {run.research_question}
          </h2>
        </div>

        {run.status === 'running' && onCancel && (
          <button className="btn btn-outline btn-sm" onClick={onCancel} style={{ color: 'var(--danger)' }}>
            <StopCircle size={14} />
            <span>Cancel Run</span>
          </button>
        )}
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-title">Iteration</div>
          <div className="metric-value">
            {run.current_iteration} / {run.max_iterations}
          </div>
          <div className="metric-desc">Loop progress</div>
        </div>

        <div className="metric-card">
          <div className="metric-title">Coverage</div>
          <div className="metric-value">{coveragePercent}%</div>
          <div className="progress-bar-wrapper">
            <div className="progress-bar-fill" style={{ width: `${coveragePercent}%` }} />
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-title">Papers Retrieved</div>
          <div className="metric-value">{run.total_papers}</div>
          <div className="metric-desc">{run.relevant_papers_count} deemed relevant</div>
        </div>

        <div className="metric-card">
          <div className="metric-title">Themes Identified</div>
          <div className="metric-value">{run.themes_count}</div>
          <div className="metric-desc">Dynamic clusters</div>
        </div>
      </div>
    </div>
  );
};
