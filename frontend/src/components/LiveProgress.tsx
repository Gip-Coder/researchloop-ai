import React, { useEffect, useRef } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Filter,
  Loader2,
  RefreshCw,
  Search,
  Sparkles,
  Terminal,
} from 'lucide-react';
import { AgentEvent } from '../types';

interface LiveProgressProps {
  events: AgentEvent[];
  isRunning: boolean;
}

export const LiveProgress: React.FC<LiveProgressProps> = ({ events, isRunning }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof bottomRef.current?.scrollIntoView === 'function') {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events]);

  const getEventIcon = (type: string, isLast: boolean) => {
    if (type.includes('failed') || type.includes('error')) {
      return <AlertTriangle size={16} className="step-icon error" />;
    }
    if (type.includes('replanning') || type.includes('replan')) {
      return <RefreshCw size={16} className="step-icon warn" />;
    }
    if (type.includes('reflection')) {
      return <AlertTriangle size={16} className="step-icon warn" />;
    }
    if (type.includes('filter')) {
      return <Filter size={16} className="step-icon ok" />;
    }
    if (type.includes('retrieval')) {
      return <Search size={16} className="step-icon ok" />;
    }
    if (isLast && isRunning) {
      return <Loader2 size={16} className="step-icon spinner" />;
    }
    return <CheckCircle2 size={16} className="step-icon ok" />;
  };

  return (
    <div className="live-feed-card">
      <div className="feed-title">
        <Terminal size={18} />
        <span>Live Agent Execution Feed</span>
        {isRunning && (
          <span
            style={{
              fontSize: '0.75rem',
              color: 'var(--primary)',
              fontWeight: 500,
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
            }}
          >
            <Loader2 size={12} className="step-icon spinner" />
            Active loop stream
          </span>
        )}
      </div>

      <div style={{ maxHeight: 380, overflowY: 'auto', paddingRight: '0.5rem' }}>
        {events.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No agent telemetry events yet. Launching loop...
          </div>
        ) : (
          events.map((evt, idx) => {
            const isLast = idx === events.length - 1;
            const eventType = evt.event_type || evt.type || '';
            const isGapWarning =
              eventType.includes('reflection') && evt.payload?.missing_topics?.length;

            return (
              <div key={evt.id || idx} className="step-item">
                {getEventIcon(eventType, isLast)}
                <div className="step-content">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
                      {evt.message}
                    </span>
                    <span className="step-time">
                      {new Date(evt.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  {isGapWarning && (
                    <div
                      style={{
                        marginTop: '0.35rem',
                        padding: '0.4rem 0.6rem',
                        backgroundColor: 'var(--warning-bg)',
                        border: '1px solid var(--warning-border)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.825rem',
                        color: '#92400e',
                      }}
                    >
                      <strong>Identified research gaps:</strong>{' '}
                      {evt.payload.missing_topics.join('; ')}
                    </div>
                  )}

                  {eventType === 'replanning.completed' && evt.payload?.new_queries && (
                    <div
                      style={{
                        marginTop: '0.35rem',
                        fontSize: '0.8rem',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      Targeted queries: {evt.payload.new_queries.slice(0, 3).join(' • ')}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};
