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
    const scope = review.research_question_and_scope;
    if (scope) {
      md += `## Research Question and Scope\n\n${scope.question}\n\n`;
      md += `Eligible papers: ${scope.eligible_papers}; papers contributing to synthesis: ${scope.papers_used}. Publication year is recorded as metadata and does not filter eligibility.\n\n`;
    }
    const methodology = review.search_and_selection_methodology;
    if (methodology) {
      md += `## Search and Selection Methodology\n\nSources: ${methodology.sources.join(', ') || 'not recorded'}. ${methodology.selection}\n\n`;
      if (methodology.queries.length) md += `Queries: ${methodology.queries.join('; ')}\n\n`;
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
    if (review.quality_warnings?.length) {
      md += `## Evidence Warnings\n\n${review.quality_warnings.map((warning) => `- ${warning}`).join('\n')}\n\n`;
    }
    if (review.limitations_of_review?.length) {
      md += `## Limitations of the Review\n\n${review.limitations_of_review.map((limitation) => `- ${limitation}`).join('\n')}\n\n`;
    }
    if (review.evidence_matrix?.length) {
      md += `## Paper-to-Theme Evidence Matrix\n\n`;
      md += `| Paper | Year | Healthcare relevance | Privacy mechanism | Accuracy | Security | Deployment | Dataset/method | Supported finding | Author limitations | Included | Evidence level |\n|---|---:|---|---|---|---|---|---|---|---|---|---|\n`;
      for (const row of review.evidence_matrix) {
        const cell = (value?: string | null) => (value || 'Unknown').replace(/\|/g, '\\|').replace(/\n/g, ' ');
        md += `| ${cell(row.title)} (${row.paper_id}) | ${row.year ?? 'Unknown'} | ${cell(row.healthcare_relevance)} | ${cell(row.privacy_mechanism)} | ${cell(row.accuracy_evaluation)} | ${cell(row.security_threat_or_defense)} | ${cell(row.deployment_context)} | ${cell(row.dataset_and_method)} | ${cell(row.main_supported_finding)} | ${cell(row.author_reported_limitations.join('; '))} | ${row.included_in_synthesis ? 'Yes' : 'No'} | ${row.evidence_level} |\n`;
      }
      for (const row of review.evidence_matrix) {
        md += `\n### ${row.title} (${row.paper_id}) — ${row.evidence_level}\n\n`;
        md += row.evidence_text ? `> ${row.evidence_text.replace(/\n/g, '\n> ')}\n` : `> Source passage unavailable.\n`;
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

        {review.research_question_and_scope && (
          <div className="review-section">
            <h2 className="review-section-heading">1. Research Question and Scope</h2>
            <p className="review-prose">{review.research_question_and_scope.question}</p>
            <p className="review-prose">{review.research_question_and_scope.papers_used} papers contributed from {review.research_question_and_scope.eligible_papers} eligible records. Publication year is recorded as metadata only.</p>
          </div>
        )}

        {review.search_and_selection_methodology && (
          <div className="review-section">
            <h2 className="review-section-heading">2. Search and Selection Methodology</h2>
            <p className="review-prose">Sources: {review.search_and_selection_methodology.sources.join(', ') || 'not recorded'}. {review.search_and_selection_methodology.selection}</p>
            {review.search_and_selection_methodology.queries.length > 0 && <p className="review-prose">Queries: {review.search_and_selection_methodology.queries.join('; ')}</p>}
          </div>
        )}

        <div className="review-section">
          <h2 className="review-section-heading">3. Executive Summary</h2>
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

        {!!review.quality_warnings?.length && (
          <div className="review-section">
            <h2 className="review-section-heading">Evidence Warnings</h2>
            <ul>{review.quality_warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul>
          </div>
        )}

        {!!review.limitations_of_review?.length && (
          <div className="review-section">
            <h2 className="review-section-heading">Limitations of the Review</h2>
            <ul>{review.limitations_of_review.map((limitation, index) => <li key={index}>{limitation}</li>)}</ul>
          </div>
        )}

        {!!review.evidence_matrix?.length && (
          <div className="review-section" style={{ overflowX: 'auto' }}>
            <h2 className="review-section-heading">Paper-to-Theme Evidence Matrix</h2>
            <table style={{ borderCollapse: 'collapse', minWidth: 1100, fontSize: '0.8rem' }}>
              <thead><tr>{['Paper', 'Year', 'Healthcare relevance', 'Privacy mechanism', 'Accuracy', 'Security', 'Deployment', 'Dataset / method', 'Supported finding', 'Author limitations', 'Themes', 'Evidence'].map((heading) => <th key={heading} style={{ textAlign: 'left', padding: '0.4rem', borderBottom: '1px solid var(--border-subtle)' }}>{heading}</th>)}</tr></thead>
              <tbody>{review.evidence_matrix.map((row) => <tr key={row.paper_id}>
                <td style={{ padding: '0.4rem' }}>{row.title} <small>({row.paper_id})</small></td>
                <td style={{ padding: '0.4rem' }}>{row.year ?? 'Unknown'}</td>
                <td style={{ padding: '0.4rem' }}>{row.healthcare_relevance || 'Unknown'}</td>
                <td style={{ padding: '0.4rem' }}>{row.privacy_mechanism || 'Unknown'}</td>
                <td style={{ padding: '0.4rem' }}>{row.accuracy_evaluation || 'Unknown'}</td>
                <td style={{ padding: '0.4rem' }}>{row.security_threat_or_defense || 'Unknown'}</td>
                <td style={{ padding: '0.4rem' }}>{row.deployment_context || 'Unknown'}</td>
                <td style={{ padding: '0.4rem' }}>{row.dataset_and_method || 'Unknown'}</td>
                <td style={{ padding: '0.4rem' }}>{row.main_supported_finding || 'Unknown'}</td>
                <td style={{ padding: '0.4rem' }}>{row.author_reported_limitations.join('; ') || 'Unknown'}</td>
                <td style={{ padding: '0.4rem' }}>{row.themes.join(', ') || 'None'}</td>
                <td style={{ padding: '0.4rem' }}>
                  {row.evidence_level}{row.included_in_synthesis ? ' · included' : ' · not included'}
                  <details><summary>Source evidence</summary><p>{row.evidence_text || 'Source passage unavailable.'}</p></details>
                </td>
              </tr>)}</tbody>
            </table>
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
