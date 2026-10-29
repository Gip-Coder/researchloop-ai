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
  preferred_min_citations?: number;
  preferred_max_citations?: number;
  strict_citation_filtering?: boolean;
  min_synthesis_papers?: number;
  target_synthesis_papers?: number;
  max_synthesis_papers?: number;
  allow_foundational_exceptions?: boolean;
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
  citation_count: number | null;
  citation_count_available?: boolean;
  matched_queries?: string[];
  is_foundational_exception?: boolean;
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
  evidence_target_met?: boolean;
  eligible_papers_count?: number;
  synthesis_papers_count?: number;
  min_synthesis_papers?: number;
  target_synthesis_papers?: number;
  max_synthesis_papers?: number;
  insufficient_evidence_warning?: string | null;
  research_question_and_scope?: {
    question: string;
    publication_year_filter?: null;
    eligible_papers: number;
    papers_used: number;
  };
  search_and_selection_methodology?: {
    sources: string[];
    queries: string[];
    selection: string;
  };
  quality_warnings?: string[];
  limitations_of_review?: string[];
  evidence_matrix?: Array<{
    paper_id: string;
    title: string;
    year?: number | null;
    source_url?: string | null;
    healthcare_relevance?: string | null;
    privacy_mechanism?: string | null;
    accuracy_evaluation?: string | null;
    security_threat_or_defense?: string | null;
    deployment_context?: string | null;
    dataset_and_method?: string | null;
    main_supported_finding?: string | null;
    author_reported_limitations: string[];
    themes: string[];
    included_in_synthesis: boolean;
    evidence_level: string;
    evidence_text?: string | null;
  }>;
  bibliography?: Array<{
    id: string;
    title: string;
    authors?: string[];
    year?: number;
    venue?: string;
    citation_count?: number | null;
    citation_count_available?: boolean;
    doi?: string;
    url?: string;
    source: string;
    is_foundational_exception?: boolean;
    matched_queries?: string[];
  }>;
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
    papers_missing_citation_data?: number;
    in_preferred_range_count?: number;
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
