import { LucideIcon } from 'lucide-react';

export type PageId =
  | 'overview'
  | 'repositories'
  | 'analysis'
  | 'dependencies'
  | 'tests'
  | 'reports';

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

