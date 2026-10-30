import { LucideIcon } from 'lucide-react';

export type PageId =
  | 'overview'
  | 'repositories'
  | 'pull-requests'
  | 'analysis'
  | 'historical'
  | 'dependencies'
  | 'tests'
  | 'reports'
  | 'settings';

export interface NavItem {
  id: PageId;
  label: string;
  icon: LucideIcon;
  badge?: string;
}

export type Theme = 'light' | 'dark';

export interface DatabaseStatus {
  connected: boolean;
  dialect: string;
  error?: string | null;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'offline';
  service: string;
  version: string;
  environment: string;
  database: DatabaseStatus;
  responseTimeMs?: number;
}

export interface AstSymbol {
  id: string;
  name: string;
  symbol_type: 'module' | 'class' | 'function' | 'method';
  file_path: string;
  line_start: number;
  line_end: number;
  docstring?: string | null;
  parent_id?: string | null;
}

export interface DependencyEdge {
  source_id: string;
  target_id: string;
  relation_type: 'imports' | 'calls' | 'inherits' | 'instantiates';
  confidence: 'confirmed' | 'inferred';
  file_path: string;
  line_number: number;
}

export interface ScanSummary {
  repo_path: string;
  commit_sha?: string | null;
  file_count: number;
  symbol_count: number;
  edge_count: number;
  symbols: AstSymbol[];
  edges: DependencyEdge[];
  duration_ms: number;
}

export interface ImpactedSymbol {
  symbol_id: string;
  symbol_name: string;
  symbol_type: 'module' | 'class' | 'function' | 'method';
  file_path: string;
  line_start: number;
  line_end: number;
  impact_type: 'direct_change' | 'direct_dependent' | 'transitive_dependent';
  depth: number;
  path_from_change: string[];
}

export interface TestRecommendation {
  test_file: string;
  test_symbol_id?: string | null;
  target_symbol_id: string;
  reason: string;
  priority: string;
}

export interface FileDiff {
  file_path: string;
  change_type: 'added' | 'modified' | 'deleted' | 'renamed' | string;
  old_path?: string | null;
  diff_content?: string;
  additions: number;
  deletions: number;
}

export interface ImpactAnalysisReport {
  repo_path: string;
  base_commit: string;
  head_commit: string;
  changed_files: string[];
  changed_symbols: AstSymbol[];
  impacted_symbols: ImpactedSymbol[];
  graph_nodes_count: number;
  graph_edges_count: number;
  recommended_tests: TestRecommendation[];
  risk_level: 'low' | 'medium' | 'elevated' | 'high';
  risk_score: number;
  summary_text: string;
  created_at: string;
  file_diffs?: FileDiff[];
}

export interface User {
  id: number;
  email: string;
  name: string;
  created_at?: string | null;
}

export interface AuthSession {
  token: string;
  user: User;
}

export interface RepositoryRecord {
  id: number;
  user_id?: number;
  name: string;
  path: string;
  default_branch: string;
  file_count: number;
  symbol_count: number;
  edge_count: number;
  is_archived?: boolean;
  last_scanned_at?: string | null;
  created_at?: string | null;
  analysis_count: number;
}

export interface AnalysisRecord {
  id: number;
  user_id?: number;
  repository_id?: number | null;
  repo_name?: string;
  repo_path?: string;
  base_commit: string;
  head_commit: string;
  pr_number?: number | null;
  pr_title?: string | null;
  is_github_pr?: boolean;
  github_comment_id?: string | null;
  analysis_engine_version?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  risk_level: 'low' | 'medium' | 'elevated' | 'high' | 'pending' | 'failed' | string;
  risk_score: number;
  changed_files_count: number;
  changed_symbols_count: number;
  impacted_symbols_count: number;
  recommended_tests_count: number;
  summary_text: string;
  error_message?: string | null;
  created_at?: string | null;
  report?: ImpactAnalysisReport | null;
}

// Phase 1: GitHub Integration Interfaces
export interface GitHubAccountStatus {
  is_connected: boolean;
  account_type?: string;
  username?: string;
  masked_token?: string;
  scopes?: string;
  avatar_url?: string;
  connected_at?: string;
}

export interface GitHubRepoItem {
  id: number;
  name: string;
  full_name: string;
  private: boolean;
  html_url: string;
  default_branch: string;
  updated_at?: string;
  is_imported?: boolean;
  local_repo_id?: number;
}

export interface GitHubPullRequest {
  number: number;
  title: string;
  state: 'open' | 'closed';
  html_url: string;
  base_ref: string;
  base_sha: string;
  head_ref: string;
  head_sha: string;
  author: string;
  updated_at: string;
  latest_analysis?: AnalysisRecord | null;
}

// Phase 2: Historical Change Intelligence Interfaces
export interface HistoricalModifiedModule {
  file_path: string;
  change_count: number;
  percentage: number;
}

export interface HistoricalImpactedComponent {
  symbol_id: string;
  impact_count: number;
  percentage: number;
}

export interface HistoricalRecurringPath {
  path: string;
  frequency: number;
}

export interface HistoricalHotspot {
  file_path: string;
  high_risk_occurrences: number;
  total_changes: number;
}

export interface HistoricalRecommendedTest {
  test: string;
  recommendation_count: number;
  percentage: number;
}

export interface HistoricalRiskTrendItem {
  analysis_id: number;
  commit: string;
  risk_score: number;
  risk_level: string;
  changed_symbols: number;
  impacted_symbols: number;
  created_at: string | null;
}

export interface HistoricalPatternsReport {
  repository_id: number;
  total_analyses: number;
  message?: string;
  frequently_modified_modules: HistoricalModifiedModule[];
  frequently_impacted_components: HistoricalImpactedComponent[];
  recurring_paths: HistoricalRecurringPath[];
  hotspots: HistoricalHotspot[];
  repeatedly_recommended_tests: HistoricalRecommendedTest[];
  risk_trend: HistoricalRiskTrendItem[];
}

export interface HistoricalAnalysisSummary {
  id: number;
  commit: string;
  created_at: string | null;
  risk_score: number;
  risk_level: string;
  changed_count: number;
  impacted_count: number;
}

export interface HistoricalComparisonResult {
  analysis_a: HistoricalAnalysisSummary;
  analysis_b: HistoricalAnalysisSummary;
  risk_score_delta: number;
  impacted_count_delta: number;
  newly_impacted_symbols: string[];
  resolved_impacted_symbols: string[];
  common_impacted_symbols: string[];
  newly_recommended_tests: string[];
  retained_tests: string[];
}

// Phase 3: Background Jobs Interface
export interface BackgroundJobStatus {
  id: string;
  job_type: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  progress_percent: number;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
  result?: any;
}


