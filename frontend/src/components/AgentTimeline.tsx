import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Eye } from 'lucide-react';
import { AgentEvent } from '../types';

interface AgentTimelineProps {
  events: AgentEvent[];
}

export const AgentTimeline: React.FC<AgentTimelineProps> = ({ events }) => {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const toggleSelect = (id: string) => {
    setSelectedId(selectedId === id ? null : id);
  };

  return (
    <div style={{ padding: '0.5rem 0' }}>
      <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>
        Agent Decision Trace & Execution Timeline
      </h3>

      <div className="trace-timeline">
        {events.map((evt, idx) => {
          const isExpanded = selectedId === evt.id;
          const hasPayload = evt.payload && Object.keys(evt.payload).length > 0;

          return (
            <div key={evt.id || idx} className="timeline-entry">
              <div className="timeline-dot" />
              <div className="timeline-card" onClick={() => hasPayload && toggleSelect(evt.id)}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span
                      style={{
                        fontSize: '0.725rem',
                        fontWeight: 600,
                        backgroundColor: '#f1f5f9',
                        padding: '0.15rem 0.45rem',
                        borderRadius: '4px',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      Iter {evt.iteration}
                    </span>
                    <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>
                      {evt.event_type || evt.type}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {new Date(evt.timestamp).toLocaleTimeString()}
                    </span>
                    {hasPayload && (
                      isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />
                    )}
                  </div>
                </div>

                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.35rem' }}>
                  {evt.message}
                </div>

                {isExpanded && hasPayload && (
                  <div
                    style={{
                      marginTop: '0.75rem',
                      padding: '0.75rem',
                      backgroundColor: '#f8fafc',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.8rem',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div style={{ fontWeight: 600, marginBottom: '0.35rem', color: 'var(--text-muted)' }}>
                      Event Payload Metadata:
                    </div>
                    <pre
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.75rem',
                        whiteSpace: 'pre-wrap',
                        color: '#334155',
                      }}
                    >
                      {JSON.stringify(evt.payload, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
