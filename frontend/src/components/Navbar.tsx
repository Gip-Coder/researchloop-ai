import React from 'react';
import { BookOpen, History, Sparkles, RefreshCw } from 'lucide-react';

interface NavbarProps {
  onNewResearch: () => void;
  onOpenHistory: () => void;
  isMockMode: boolean;
  activeRunQuestion?: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  onNewResearch,
  onOpenHistory,
  isMockMode,
}) => {
  return (
    <header className="header-nav">
      <div className="header-content">
        <div className="brand-wrapper" onClick={onNewResearch}>
          <div className="brand-logo">
            <BookOpen size={18} />
          </div>
          <span className="brand-name">ResearchLoop AI</span>
          <span className="brand-badge">Autonomous Literature Review</span>
          {isMockMode && (
            <span
              style={{
                fontSize: '0.7rem',
                fontWeight: 600,
                backgroundColor: '#ecfdf5',
                color: '#059669',
                border: '1px solid #a7f3d0',
                padding: '0.15rem 0.5rem',
                borderRadius: '9999px',
              }}
            >
              Mock Mode (Offline)
            </span>
          )}
        </div>

        <div className="header-actions">
          <button className="btn btn-outline btn-sm" onClick={onOpenHistory} title="View previous research runs">
            <History size={14} />
            <span>History</span>
          </button>
          <button className="btn btn-primary btn-sm" onClick={onNewResearch}>
            <Sparkles size={14} />
            <span>New Review</span>
          </button>
        </div>
      </div>
    </header>
  );
};
