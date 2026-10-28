import React, { useState, useMemo } from 'react';
import { ExternalLink, Filter, Search, SortAsc, CheckCircle2, XCircle, Award } from 'lucide-react';
import { Paper } from '../types';

interface PaperExplorerProps {
  papers: Paper[];
}

export const PaperExplorer: React.FC<PaperExplorerProps> = ({ papers }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sourceFilter, setSourceFilter] = useState('all');
  const [relevanceFilter, setRelevanceFilter] = useState('all');
  const [sortBy, setSortBy] = useState<'relevance' | 'citations' | 'year' | 'title'>('relevance');

  const filteredPapers = useMemo(() => {
    return papers
      .filter((p) => {
        // Search term in title, abstract, or authors
        if (searchTerm) {
          const term = searchTerm.toLowerCase();
          const inTitle = p.title.toLowerCase().includes(term);
          const inAbstract = p.abstract?.toLowerCase().includes(term) ?? false;
          const inAuthors = p.authors.some((a) => a.toLowerCase().includes(term));
          if (!inTitle && !inAbstract && !inAuthors) return false;
        }

        // Source filter
        if (sourceFilter !== 'all' && p.source.toLowerCase() !== sourceFilter.toLowerCase()) {
          return false;
        }

        // Relevance filter
        if (relevanceFilter === 'relevant' && p.is_relevant !== true) return false;
        if (relevanceFilter === 'rejected' && p.is_relevant !== false) return false;

        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'relevance') {
          return (b.relevance_score || 0) - (a.relevance_score || 0);
        }
        if (sortBy === 'citations') {
          const aCit = a.citation_count !== null && a.citation_count !== undefined ? a.citation_count : -1;
          const bCit = b.citation_count !== null && b.citation_count !== undefined ? b.citation_count : -1;
          return bCit - aCit;
        }
        if (sortBy === 'year') {
          return (b.year || 0) - (a.year || 0);
        }
        if (sortBy === 'title') {
          return a.title.localeCompare(b.title);
        }
        return 0;
      });
  }, [papers, searchTerm, sourceFilter, relevanceFilter, sortBy]);

  const isSafeUrl = (url?: string) => {
    if (!url) return false;
    return url.startsWith('http://') || url.startsWith('https://');
  };

  return (
    <div>
      <div className="papers-toolbar">
        <div className="search-input-wrapper">
          <Search size={16} className="search-input-icon" />
          <input
            type="text"
            aria-label="Search papers"
            className="search-input-field"
            placeholder="Search papers by keyword, concept, or author..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <select
            aria-label="Filter by source"
            className="config-select"
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
          >
            <option value="all">All Academic Sources</option>
            <option value="arxiv">arXiv</option>
            <option value="crossref">Crossref</option>
            <option value="semantic_scholar">Semantic Scholar</option>
          </select>

          <select
            aria-label="Filter by relevance"
            className="config-select"
            value={relevanceFilter}
            onChange={(e) => setRelevanceFilter(e.target.value)}
          >
            <option value="all">All Candidate Papers</option>
            <option value="relevant">Relevant Only</option>
            <option value="rejected">Rejected Only</option>
          </select>

          <select
            aria-label="Sort papers"
            className="config-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
          >
            <option value="relevance">Sort: Relevance Score</option>
            <option value="citations">Sort: Citations Count</option>
            <option value="year">Sort: Publication Year</option>
            <option value="title">Sort: Title (A-Z)</option>
          </select>
        </div>
      </div>

      <div style={{ marginBottom: '1rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
        Showing {filteredPapers.length} of {papers.length} literature records
      </div>

      {filteredPapers.length === 0 ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          No papers match your search and filter criteria.
        </div>
      ) : (
        filteredPapers.map((paper) => {
          const relevancePct = paper.relevance_score !== null && paper.relevance_score !== undefined
            ? Math.round(paper.relevance_score * 100)
            : null;
          const hasCitations = paper.citation_count !== null && paper.citation_count !== undefined;
          const isPreferredCitationRange = hasCitations && (paper.citation_count! >= 10 && paper.citation_count! <= 15);

          return (
            <div key={paper.id} className="paper-card">
              <div className="paper-header">
                <div>
                  <h4 className="paper-title">{paper.title}</h4>
                  <div className="paper-authors">
                    {paper.authors.length > 0 ? paper.authors.join(', ') : 'Unknown Authors'}
                  </div>
                </div>

                {paper.is_relevant !== undefined && paper.is_relevant !== null && (
                  <span
                    className={`status-badge ${
                      paper.is_relevant ? 'badge-completed' : 'badge-failed'
                    }`}
                  >
                    {paper.is_relevant ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
                    <span>{paper.is_relevant ? `Relevant (${relevancePct}%)` : 'Rejected'}</span>
                  </span>
                )}
              </div>

              <div className="paper-meta-row">
                <span className="source-badge">{paper.source}</span>
                {paper.year && <span>Year: {paper.year}</span>}
                {paper.venue && <span>Venue: {paper.venue}</span>}
                <span
                  style={{
                    color: isPreferredCitationRange ? 'var(--primary)' : 'inherit',
                    fontWeight: isPreferredCitationRange ? 600 : 'normal',
                  }}
                >
                  Citations: {hasCitations ? paper.citation_count!.toLocaleString() : 'Unavailable'}
                  {isPreferredCitationRange && ' (Preferred 10-15)'}
                </span>

                {paper.is_foundational_exception && (
                  <span
                    style={{
                      fontSize: '0.72rem',
                      padding: '0.1rem 0.4rem',
                      borderRadius: '4px',
                      backgroundColor: '#fef3c7',
                      color: '#92400e',
                      fontWeight: 600,
                    }}
                  >
                    Foundational Exception
                  </span>
                )}

                {paper.doi && (
                  <a
                    href={`https://doi.org/${paper.doi}`}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.2rem',
                      color: 'var(--primary)',
                      textDecoration: 'none',
                    }}
                  >
                    <span>DOI</span>
                    <ExternalLink size={12} />
                  </a>
                )}
                {paper.url && !paper.doi && isSafeUrl(paper.url) && (
                  <a
                    href={paper.url}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.2rem',
                      color: 'var(--primary)',
                      textDecoration: 'none',
                    }}
                  >
                    <span>Link</span>
                    <ExternalLink size={12} />
                  </a>
                )}
              </div>

              {paper.abstract && (
                <p className="paper-abstract">
                  {paper.abstract.length > 320
                    ? `${paper.abstract.slice(0, 320)}...`
                    : paper.abstract}
                </p>
              )}

              {paper.relevance_reason && (
                <div className="relevance-box">
                  <strong>Relevance Assessment:</strong> {paper.relevance_reason}
                </div>
              )}

              {paper.matched_queries && paper.matched_queries.length > 0 && (
                <div style={{ marginTop: '0.4rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <strong>Retrieved by query:</strong> {paper.matched_queries.join('; ')}
                </div>
              )}
            </div>
          );
        })
      )}
    </div>
  );
};
