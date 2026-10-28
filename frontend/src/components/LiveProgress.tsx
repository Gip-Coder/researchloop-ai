import React, { useEffect, useRef, useState, useMemo } from 'react';
import {
  AlertTriangle,
  ArrowDown,
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

const STAGES = [
  { key: 'plan', label: 'Planning', match: ['planner.started', 'planner.completed'] },
  { key: 'retrieval', label: 'Retrieval', match: ['retrieval.started', 'retrieval.completed', 'retrieval.failed'] },
  { key: 'filter', label: 'Filtering & Ranking', match: ['filter.completed'] },
  { key: 'synthesis', label: 'Thematic Synthesis', match: ['synthesis.started', 'synthesis.completed'] },
  { key: 'reflection', label: 'Critic Evaluation', match: ['reflection.started', 'reflection.completed'] },
  { key: 'replanning', label: 'Replanning / Finalizing', match: ['replanning.started', 'replanning.completed', 'research.completed'] },
];

export const LiveProgress: React.FC<LiveProgressProps> = ({ events, isRunning }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoFollow, setAutoFollow] = useState(true);

  // Determine active stage from events
  const currentStageIndex = useMemo(() => {
    if (!events.length) return 0;
    const lastEvent = events[events.length - 1];
    const lastType = lastEvent.event_type || lastEvent.type || '';
    for (let i = STAGES.length - 1; i >= 0; i--) {
      if (STAGES[i].match.some((m) => lastType.includes(m) || m.includes(lastType))) {
        return i;
      }
    }
    return 0;
  }, [events]);

  // Handle user manual scrolling to pause / resume auto-follow
  const handleScroll = () => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 40;
    if (isNearBottom !== autoFollow) {
      setAutoFollow(isNearBottom);
    }
  };

  // Auto-scroll when new events arrive if autoFollow is active
  useEffect(() => {
    if (!autoFollow || !containerRef.current) return;
    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    requestAnimationFrame(() => {
    try {
      if (containerRef.current) {
        if (typeof containerRef.current.scrollTo === 'function') {
          containerRef.current.scrollTo({
            top: containerRef.current.scrollHeight,
            behavior: prefersReducedMotion ? 'auto' : 'smooth',
          });
        } else {
          containerRef.current.scrollTop = containerRef.current.scrollHeight;
        }
      }
    } catch {
      // Ignore scroll errors in mock/headless DOM environments
    }
    });
  }, [events, autoFollow]);

  const resumeAutoFollow = () => {
    setAutoFollow(true);
    try {
      if (containerRef.current) {
        if (typeof containerRef.current.scrollTo === 'function') {
          containerRef.current.scrollTo({
            top: containerRef.current.scrollHeight,
            behavior: 'smooth',
          });
        } else {
          containerRef.current.scrollTop = containerRef.current.scrollHeight;
        }
      }
    } catch {
      // Ignore scroll errors in headless/test DOM environments
    }
  };

  const formatEventTime = (isoStr?: string) => {
    if (!isoStr) return '';
    try {
      const d = new Date(isoStr);
      if (isNaN(d.getTime())) return '';
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return '';
    }
  };

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
    <div className="live-feed-card" style={{ position: 'relative' }}>
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

      {/* Progress Stage Tracker */}
      <div
        style={{
          display: 'flex',
          gap: '0.25rem',
          padding: '0.5rem 0',
          marginBottom: '0.75rem',
          borderBottom: '1px solid var(--border-subtle)',
          overflowX: 'auto',
        }}
        aria-label="Research Stages"
      >
        {STAGES.map((stg, idx) => {
          const isDone = idx < currentStageIndex || (!isRunning && events.length > 0);
          const isCurrent = idx === currentStageIndex && isRunning;

          return (
            <div
              key={stg.key}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.25rem',
                fontSize: '0.72rem',
                padding: '0.2rem 0.45rem',
                borderRadius: '4px',
                whiteSpace: 'nowrap',
                backgroundColor: isCurrent ? 'var(--primary-subtle, #eff6ff)' : isDone ? '#f8fafc' : 'transparent',
                color: isCurrent ? 'var(--primary)' : isDone ? 'var(--text-secondary)' : 'var(--text-muted)',
                fontWeight: isCurrent ? 600 : 500,
                border: isCurrent ? '1px solid var(--primary)' : '1px solid transparent',
              }}
            >
              {isCurrent && <Loader2 size={10} className="step-icon spinner" />}
              {isDone && !isCurrent && <CheckCircle2 size={10} style={{ color: 'var(--success)' }} />}
              <span>{stg.label}</span>
              {idx < STAGES.length - 1 && <span style={{ color: 'var(--border-subtle)', marginLeft: '0.25rem' }}>›</span>}
            </div>
          );
        })}
      </div>

      {/* Scrollable Event Feed Container */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        style={{
          maxHeight: 380,
          overflowY: 'auto',
          paddingRight: '0.5rem',
          scrollBehavior: 'smooth',
        }}
      >
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
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
                    <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
                      {evt.message}
                    </span>
                    <span className="step-time" style={{ whiteSpace: 'nowrap', flexShrink: 0 }}>
                      {formatEventTime(evt.timestamp)}
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
                      <strong>Targeted follow-up queries:</strong>
                      <ul style={{ margin: '0.2rem 0 0 1rem', padding: 0 }}>
                        {evt.payload.new_queries.map((q: string, qIdx: number) => (
                          <li key={qIdx}>{q}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Auto-scroll resume control pill */}
      {!autoFollow && isRunning && (
        <button
          onClick={resumeAutoFollow}
          aria-label="Resume auto-scrolling to latest events"
          style={{
            position: 'absolute',
            bottom: '1rem',
            right: '1.5rem',
            backgroundColor: 'var(--primary)',
            color: '#fff',
            border: 'none',
            borderRadius: '999px',
            padding: '0.35rem 0.75rem',
            fontSize: '0.75rem',
            fontWeight: 500,
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.35rem',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            cursor: 'pointer',
            zIndex: 10,
          }}
        >
          <ArrowDown size={12} />
          Follow latest
        </button>
      )}
    </div>
  );
};
