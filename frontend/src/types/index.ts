export type RunStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface ResearchConfigInput {
  max_iterations?: number;
  target_coverage?: number;
  min_new_relevant_papers?: number;
  mock_mode?: boolean;
  llm_provider?: string;
  llm_model?: string;
  preferred_sources?: string[];
  temperature?: number;
}

export interface ResearchRun {
  id: string;
  research_question: string;
  status: RunStatus;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  current_iteration: number;
  max_iterations: number;
  coverage: number;
  stopping_reason?: string;
  error?: string;
  total_papers: number;
  relevant_papers_count: number;
  themes_count: number;
  iterations_count: number;
}

export interface ResearchIteration {
  id: string;
  run_id: string;
  iteration_number: number;
  search_plan?: {
    research_question?: string;
    sub_questions?: string[];
    keywords?: string[];
    search_queries?: string[];
    preferred_sources?: string[];
    inclusion_criteria?: string[];
    exclusion_criteria?: string[];
  };
  queries: string[];
  retrieved_count: number;
  new_papers_count: number;
  relevant_count: number;
  coverage: number;
  reflection?: {
    coverage_score: number;
    relevance_score: number;
    missing_topics: string[];
    weak_areas: string[];
    contradictions: string[];
    outdated_areas: string[];
    recommended_queries: string[];
    should_replan: boolean;
    reason: string;
    evaluation_type: string;
  };
  created_at: string;
}

export interface Paper {
  id: string;
  title: string;
  authors: string[];
  abstract?: string;
  year?: number;
  venue?: string;
  doi?: string;
  url?: string;
  source: string;
  citation_count: number;
  publication_date?: string;
  categories: string[];
  is_relevant?: boolean;
  relevance_score?: number;
  relevance_reason?: string;
  iteration_number?: number;
}

export interface Theme {
  id: string;
  theme_id: string;
  title: string;
  description: string;
  paper_ids: string[];
  key_findings: string[];
  contradictions_or_tensions: string[];
}

export interface AgentEvent {
  id: string;
  run_id: string;
  event_type: string;
  type?: string;
  iteration: number;
  message: string;
  timestamp: string;
  payload: Record<string, any>;
}

export interface FinalReview {
  title: string;
  narrative: string;
  key_themes: Array<{
    title: string;
    description: string;
    paper_count: number;
    key_findings: string[];
  }>;
  consensus_findings: string[];
  open_research_gaps: string[];
  coherence_score: number;
  relevance_score: number;
}

export interface ResearchResultData {
  run_id: string;
  research_question: string;
  status: RunStatus;
  coverage_score: number;
  stop_reason?: string;
  final_review?: FinalReview;
  synthesis?: {
    paper_analyses?: Array<{
      paper_id: string;
      title: string;
      research_problem: string;
      methodology: string;
      dataset?: string;
      key_findings: string[];
      contribution: string;
      limitations: string[];
      relevance: string;
    }>;
    themes?: Theme[];
    agreements?: string[];
    differences?: string[];
    contradictions?: string[];
    methodological_differences?: string[];
    trends?: string[];
    research_gaps?: string[];
    narrative_summary?: string;
  };
  reflection?: {
    coverage_score: number;
    relevance_score: number;
    missing_topics: string[];
    weak_areas: string[];
    contradictions: string[];
    outdated_areas: string[];
    recommended_queries: string[];
    should_replan: boolean;
    reason: string;
  };
  metadata: Record<string, any>;
}

export interface EvaluationData {
  run_id: string;
  coverage: number;
  relevance: number;
  coherence: number;
  citation_distribution: {
    total_citations?: number;
    mean_citations?: number;
    median_citations?: number;
    max_citations?: number;
    papers_with_citation_data?: number;
  };
  topic_coverage?: number;
  paper_recall?: number;
  evaluation_type: 'intrinsic' | 'benchmark';
  benchmark_comparison?: {
    paper_recall: number;
    found_key_papers: string[];
    missed_key_papers: string[];
    topic_overlap_score: number;
    covered_topics: string[];
    missed_topics: string[];
    finding_alignment_score: number;
    summary: string;
  };
}
