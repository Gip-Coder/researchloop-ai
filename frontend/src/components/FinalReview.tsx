import React, { useState } from 'react';
import { Copy, Download, Check, BookOpen, Layers } from 'lucide-react';
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
  const relevantPapers = papers.filter((p) => p.is_relevant === true);

  const generateMarkdown = () => {
    let md = `# ${review.title}\n\n`;
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
    md += `## References\n\n`;
    relevantPapers.forEach((p, idx) => {
      md += `[${idx + 1}] ${p.authors.join(', ')} (${p.year || 'n.d.'}). *${p.title}*. ${p.venue || p.source}. ${p.doi ? `https://doi.org/${p.doi}` : p.url || ''}\n`;
    });
    return md;
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
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginBottom: '1rem' }}>
        <button className="btn btn-outline btn-sm" onClick={handleCopy}>
          {copied ? <Check size={14} style={{ color: 'var(--success)' }} /> : <Copy size={14} />}
          <span>{copied ? 'Copied Markdown' : 'Copy as Markdown'}</span>
        </button>
        <button className="btn btn-outline btn-sm" onClick={handleDownload}>
          <Download size={14} />
          <span>Download .MD</span>
        </button>
      </div>

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
            {relevantPapers.map((paper, idx) => (
              <li key={paper.id || idx} style={{ marginBottom: '0.5rem' }}>
                <strong>{paper.authors.length > 0 ? paper.authors.join(', ') : 'Unknown'}</strong>{' '}
                ({paper.year || 'n.d.'}). <em>{paper.title}</em>.{' '}
                {paper.venue ? `${paper.venue}. ` : ''}
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
                  paper.url && (
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
