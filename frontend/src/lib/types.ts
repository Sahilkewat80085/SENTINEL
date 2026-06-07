// Shared API Types and Interfaces

export interface ResponseEnvelope<T> {
  success: boolean;
  data: T | null;
  meta: MetaData | null;
  errors: ErrorDetail[] | null;
}

export interface MetaData {
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  generated_at: string;
}

export interface ErrorDetail {
  code: string;
  field?: string;
  message: string;
}

// Auth Types
export interface Token {
  access_token: string;
  token_type: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: string; // 'admin' | 'manager' | 'viewer'
  is_active: boolean;
  created_at: string;
  last_login_at?: string;
}

// Repository Types
export interface Repository {
  id: string;
  name: string;
  url: string;
  default_branch: string;
  folders: string[];
  jira_patterns: string[];
  sync_mode: string; // 'api' | 'git' | 'hybrid'
  sync_interval: number;
  is_active: boolean;
  last_synced_at?: string;
  last_sync_sha?: string;
  created_at: string;
  updated_at: string;
}

// Commit Types
export interface Author {
  name: string;
  email: string;
  github_username?: string;
}

export interface CommitFile {
  file_path: string;
  folder?: string;
  change_type: string; // 'ADDED' | 'MODIFIED' | 'DELETED' | 'RENAMED'
  additions: number;
  deletions: number;
}

export interface Commit {
  id: string;
  sha: string;
  repository_id: string;
  branch?: string;
  message: string;
  commit_date: string;
  ingested_at: string;
  author: Author;
}

export interface CommitDetail extends Commit {
  files: CommitFile[];
  jiras: string[];
}

// Jira Types
export interface JiraSummary {
  jira_id: string;
  repository_id: string;
  commit_count: number;
  author_count: number;
  first_seen: string;
  last_updated: string;
  touched_folders: string[];
  folder_count: number;
  status: string; // 'ACTIVE' | 'STALE' | 'DORMANT' | 'ARCHIVED'
}

export interface JiraTimelineItem {
  sha: string;
  message: string;
  commit_date: string;
  author_name: string;
  author_email: string;
  folders: string[];
  files_count: number;
}

export interface JiraDetail {
  summary: JiraSummary;
  timeline: JiraTimelineItem[];
}

// Coverage Types
export interface FolderCoverageDetail {
  folder_name: string;
  is_merged: boolean;
  merge_date?: string;
}

export interface JiraCoverageRow {
  jira_id: string;
  folders: FolderCoverageDetail[];
  coverage_pct: number;
  status: string; // 'MERGED' | 'PARTIAL' | 'MISSING'
}

export interface CoverageMatrix {
  repository_id: string;
  folders_list: string[];
  rows: JiraCoverageRow[];
}

export interface CoverageSummary {
  total_jiras: number;
  merged_count: number;
  partial_count: number;
  missing_count: number;
  overall_coverage_pct: number;
}

export interface MissingMerge {
  jira_id: string;
  folder: string;
  last_updated: string;
}

// Content Verification Types
export interface ContentVerificationResult {
  file_path: string;
  status: string; // 'IDENTICAL' | 'DIFFERENT' | 'MISSING'
  drift_score: number;
  folder_hashes: Record<string, string>;
  majority_hash?: string;
  divergent_folders: string[];
  file_sizes: Record<string, number>;
}

export interface DriftReport {
  drifted_files: ContentVerificationResult[];
  overall_drift_score: number;
}

// Merge Delay Types
export interface FolderDelayRank {
  folder_name: string;
  avg_delay_days: number;
  max_delay_days: number;
  p95_delay_days: number;
}

export interface DelayResult {
  jira_id: string;
  initial_commit_date: string;
  folder_merge_dates: Record<string, string | null>;
  propagation_delay_days?: number;
  status: string; // 'HEALTHY' | 'WARNING' | 'CRITICAL'
}

export interface DelayStatistics {
  overall_avg_delay_days: number;
  overall_max_delay_days: number;
  status_distribution: Record<string, number>;
  folder_rankings: FolderDelayRank[];
}

// Folder Health Types
export interface FolderHealthResult {
  folder_name: string;
  coverage_score: number;
  consistency_score: number;
  timeliness_score: number;
  completeness_score: number;
  health_score: number;
  classification: string; // 'EXCELLENT' | 'GOOD' | 'WARNING' | 'POOR' | 'CRITICAL'
}

export interface FolderHealthRank {
  folder_name: string;
  health_score: number;
  classification: string;
  rank: number;
}

export interface HeatmapCell {
  folder_name: string;
  metric: 'coverage' | 'consistency' | 'timeliness' | 'completeness' | 'health';
  score: number;
}

// Exception Detection/Violation Types
export interface RuleViolation {
  id: string;
  repository_id: string;
  rule_id: string;
  severity: string; // 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  category: string; // 'COVERAGE' | 'DELAY' | 'CONSISTENCY'
  jira_id?: string;
  folder_name?: string;
  file_path?: string;
  description: string;
  details: Record<string, any>;
  is_acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
  acknowledge_note?: string;
  detected_at: string;
  resolved_at?: string;
}

export interface ViolationSummary {
  total_violations: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  acknowledged_count: number;
  unacknowledged_count: number;
  by_category: Record<string, number>;
}

// Trend Analytics Types
export interface TrendPoint {
  date: string;
  value: number;
}

export interface FolderTrendPoint {
  date: string;
  folder_name: string;
  health_score: number;
  coverage_score: number;
  consistency_score: number;
  timeliness_score: number;
  completeness_score: number;
}

export interface ViolationTrendPoint {
  date: string;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  total_count: number;
}

// Dashboard Summary types
export interface GovernanceScoreDetail {
  score: number;
  grade: string;
  folder_health_average: number;
  violation_penalty: number;
  active_critical_count: number;
  active_high_count: number;
  active_medium_count: number;
  active_low_count: number;
}

export interface DashboardKPICards {
  total_jiras: number;
  overall_coverage_pct: number;
  avg_propagation_delay_days: number;
  active_violations_count: number;
}

export interface RecentActivity {
  id: string;
  timestamp: string;
  activity_type: string; // 'sync' | 'violation_detected' | 'violation_acknowledged'
  description: string;
  details: Record<string, any>;
}

export interface DashboardSummary {
  kpis: DashboardKPICards;
  governance_score: GovernanceScoreDetail;
  recent_activity: RecentActivity[];
  critical_items: RuleViolation[];
}
