import React, { useState } from 'react';
import { Copy, Download, Check, BookOpen, Layers, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { Paper, ResearchResultData } from '../types';

interface FinalReviewProps {
  result?: ResearchResultData;
  papers: Paper[];
}

export const FinalReview: React.FC<FinalReviewProps> = ({ result, papers }) => {
  const [copied, setCopied] = useState(false);

  if (!result || !result.final_review) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        Final literature review synthesis will be rendered once the research loop reaches its
        stopping criteria.
      </div>
    );
  }

  const review = result.final_review;
  // Use review bibliography if provided, otherwise filter relevant papers
  const relevantPapers = papers.filter((p) => p.is_relevant === true);
  const bibPapers = review.bibliography && review.bibliography.length > 0
    ? review.bibliography
    : relevantPapers;

  const generateMarkdown = () => {
    let md = `# ${review.title}\n\n`;
    if (review.insufficient_evidence_warning) {
      md += `> **Notice**: ${review.insufficient_evidence_warning}\n\n`;
    }
    md += `## Executive Summary\n\n${review.narrative}\n\n`;
    md += `## Key Thematic Findings\n\n`;
    for (const t of review.key_themes || []) {
      md += `### ${t.title} (${t.paper_count} papers)\n`;
      md += `${t.description}\n\n`;
      for (const f of t.key_findings || []) {
        md += `- ${f}\n`;
      }
      md += `\n`;
    }
    if (review.consensus_findings?.length) {
      md += `## Areas of Consensus\n\n`;
      for (const c of review.consensus_findings) {
        md += `- ${c}\n`;
      }
      md += `\n`;
    }
    if (review.open_research_gaps?.length) {
      md += `## Open Research Gaps\n\n`;
      for (const g of review.open_research_gaps) {
        md += `- ${g}\n`;
      }
      md += `\n`;
    }
    md += `## References (${bibPapers.length} Papers)\n\n`;
    bibPapers.forEach((p, idx) => {
      const authors = p.authors && p.authors.length > 0 ? p.authors.join(', ') : 'Unknown Authors';
      const citStr = p.citation_count !== null && p.citation_count !== undefined ? ` [Citations: ${p.citation_count}]` : '';
      const foundStr = p.is_foundational_exception ? ' [Foundational Exception]' : '';
      md += `[${idx + 1}] ${authors} (${p.year || 'n.d.'}). *${p.title}*. ${p.venue || p.source}.${citStr}${foundStr} ${p.doi ? `https://doi.org/${p.doi}` : p.url || ''}\n`;
    });
    return md;
  };

  const isSafeUrl = (url?: string) => {
    if (!url) return false;
    return url.startsWith('http://') || url.startsWith('https://');
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(generateMarkdown());
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([generateMarkdown()], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Literature_Review_${result.run_id.slice(0, 8)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span
            style={{
              fontSize: '0.8rem',
              fontWeight: 600,
              padding: '0.2rem 0.6rem',
              borderRadius: '999px',
              backgroundColor: review.evidence_target_met !== false ? '#ecfdf5' : '#fffbeb',
              color: review.evidence_target_met !== false ? '#065f46' : '#92400e',
              border: review.evidence_target_met !== false ? '1px solid #a7f3d0' : '1px solid #fde68a',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.3rem',
            }}
          >
            {review.evidence_target_met !== false ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
            <span>Evidence pool: {bibPapers.length} synthesized papers (Target: 6–10)</span>
          </span>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-outline btn-sm" onClick={handleCopy}>
            {copied ? <Check size={14} style={{ color: 'var(--success)' }} /> : <Copy size={14} />}
            <span>{copied ? 'Copied Markdown' : 'Copy as Markdown'}</span>
          </button>
          <button className="btn btn-outline btn-sm" onClick={handleDownload}>
            <Download size={14} />
            <span>Download .MD</span>
          </button>
        </div>
      </div>

      {review.insufficient_evidence_warning && (
        <div
          style={{
            padding: '0.75rem 1rem',
            backgroundColor: '#fffbeb',
            border: '1px solid #fde68a',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1rem',
            color: '#92400e',
            fontSize: '0.875rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <AlertTriangle size={16} style={{ flexShrink: 0 }} />
          <span>{review.insufficient_evidence_warning}</span>
        </div>
      )}

      <article className="literature-review-doc">
        <h1 className="review-doc-title">{review.title}</h1>

        <div className="review-section">
          <h2 className="review-section-heading">1. Executive Summary & Synthesis</h2>
          <p className="review-prose">{review.narrative}</p>
        </div>

        <div className="review-section">
          <h2 className="review-section-heading">2. Thematic Analysis of the Literature</h2>
          {(review.key_themes || []).map((theme, idx) => (
            <div key={idx} style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--primary)', marginBottom: '0.35rem' }}>
                2.{idx + 1}. {theme.title}
              </h3>
              <p className="review-prose" style={{ fontSize: '0.975rem', marginBottom: '0.5rem' }}>
                {theme.description}
              </p>
              <ul style={{ paddingLeft: '1.5rem', fontSize: '0.925rem', color: 'var(--text-secondary)' }}>
                {(theme.key_findings || []).map((f, fIdx) => (
                  <li key={fIdx} style={{ marginBottom: '0.25rem' }}>{f}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {review.consensus_findings?.length > 0 && (
          <div className="review-section">
            <h2 className="review-section-heading">3. Consensus Findings Across Studies</h2>
            <ul style={{ paddingLeft: '1.5rem', fontSize: '0.975rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
              {review.consensus_findings.map((finding, idx) => (
                <li key={idx} style={{ marginBottom: '0.4rem' }}>{finding}</li>
              ))}
            </ul>
          </div>
        )}

        {review.open_research_gaps?.length > 0 && (
          <div className="review-section">
            <h2 className="review-section-heading">4. Open Research Gaps & Future Directions</h2>
            <ul style={{ paddingLeft: '1.5rem', fontSize: '0.975rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
              {review.open_research_gaps.map((gap, idx) => (
                <li key={idx} style={{ marginBottom: '0.4rem' }}>{gap}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="review-section" style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '1.5rem' }}>
          <h2 className="review-section-heading">5. Curated Academic Bibliography</h2>
          <ol style={{ paddingLeft: '1.5rem', fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.8 }}>
            {bibPapers.map((paper, idx) => (
              <li key={paper.id || idx} style={{ marginBottom: '0.5rem' }}>
                <strong>{paper.authors && paper.authors.length > 0 ? paper.authors.join(', ') : 'Unknown Authors'}</strong>{' '}
                ({paper.year || 'n.d.'}). <em>{paper.title}</em>.{' '}
                {paper.venue ? `${paper.venue}. ` : ''}
                {paper.citation_count !== null && paper.citation_count !== undefined && (
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginRight: '0.35rem' }}>
                    [Citations: {paper.citation_count}]
                  </span>
                )}
                {paper.is_foundational_exception && (
                  <span style={{ color: '#92400e', backgroundColor: '#fef3c7', padding: '0.1rem 0.35rem', borderRadius: '3px', fontSize: '0.75rem', marginRight: '0.35rem' }}>
                    Foundational Exception
                  </span>
                )}
                {paper.doi ? (
                  <a
                    href={`https://doi.org/${paper.doi}`}
                    target="_blank"
                    rel="noreferrer"
                    style={{ color: 'var(--primary)', textDecoration: 'none' }}
                  >
                    https://doi.org/{paper.doi}
                  </a>
                ) : (
                  paper.url && isSafeUrl(paper.url) && (
                    <a
                      href={paper.url}
                      target="_blank"
                      rel="noreferrer"
                      style={{ color: 'var(--primary)', textDecoration: 'none' }}
                    >
                      {paper.url}
                    </a>
                  )
                )}
              </li>
            ))}
          </ol>
        </div>
      </article>
    </div>
  );
};
