import axios from 'axios';
import { 
  ResponseEnvelope, Token, User, Repository, Commit, CommitDetail, 
  JiraSummary, JiraDetail, CoverageMatrix, CoverageSummary, MissingMerge, 
  DriftReport, DelayStatistics, FolderHealthResult, HeatmapCell, 
  RuleViolation, ViolationSummary, TrendPoint, FolderTrendPoint, 
  ViolationTrendPoint, DashboardSummary, GovernanceScoreDetail, DashboardKPICards,
  FolderDelayRank, FolderHealthRank
} from './types';

// In Docker behind Nginx: NEXT_PUBLIC_API_URL is not set, so calls go to /api/v1 (relative, proxied by Nginx)
// In local dev (no nginx): set NEXT_PUBLIC_API_URL=http://localhost:8000
const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('sentinel_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor (no auth redirect)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(error);
  }
);

// Helper to extract data from envelope
const handleResponse = <T>(response: any): T => {
  const envelope = response.data as ResponseEnvelope<T>;
  if (envelope.success && envelope.data !== null && envelope.data !== undefined) {
    return envelope.data;
  }
  throw new Error(envelope.errors?.[0]?.message || 'API request failed');
};

export const apiService = {
  // Authentication
  auth: {
    login: async (username: string, password: string): Promise<Token> => {
      // Backend uses OAuth2PasswordRequestForm by default, which takes form data, or JSON depending on app/api/v1/auth.py
      // Let's support both but check backend auth code. Pydantic UserLogin takes username & password as JSON.
      const res = await api.post('/auth/login', { username, password });
      return handleResponse<Token>(res);
    },
    getProfile: async (): Promise<User> => {
      const res = await api.get('/auth/me');
      return handleResponse<User>(res);
    },
  },

  // Repositories
  repositories: {
    list: async (): Promise<Repository[]> => {
      const res = await api.get('/repositories');
      return handleResponse<Repository[]>(res);
    },
    create: async (data: Partial<Repository>): Promise<Repository> => {
      const res = await api.post('/repositories', data);
      return handleResponse<Repository>(res);
    },
    get: async (id: string): Promise<Repository> => {
      const res = await api.get(`/repositories/${id}`);
      return handleResponse<Repository>(res);
    },
    update: async (id: string, data: Partial<Repository>): Promise<Repository> => {
      const res = await api.put(`/repositories/${id}`, data);
      return handleResponse<Repository>(res);
    },
    delete: async (id: string): Promise<void> => {
      await api.delete(`/repositories/${id}`);
    },
    sync: async (id: string): Promise<{ task_id: string; message: string }> => {
      const res = await api.post(`/repositories/${id}/sync`);
      return handleResponse<{ task_id: string; message: string }>(res);
    },
    syncStatus: async (id: string): Promise<{ status: string; progress?: number; last_synced_at?: string }> => {
      const res = await api.get(`/repositories/${id}/sync/status`);
      return handleResponse<{ status: string; progress?: number; last_synced_at?: string }>(res);
    },
  },

  // Commits
  commits: {
    list: async (page = 1, pageSize = 50, author?: string, folder?: string, query?: string): Promise<{ items: Commit[], total: number }> => {
      const params: any = { page, page_size: pageSize };
      if (author) params.author = author;
      if (folder) params.folder = folder;
      if (query) params.query = query;
      const res = await api.get('/commits', { params });
      const data = handleResponse<Commit[]>(res);
      return { items: data, total: res.data.meta?.total || 0 };
    },
    get: async (sha: string): Promise<CommitDetail> => {
      const res = await api.get(`/commits/${sha}`);
      return handleResponse<CommitDetail>(res);
    },
  },

  // Jiras
  jiras: {
    list: async (page = 1, pageSize = 50, status?: string, query?: string): Promise<{ items: JiraSummary[], total: number }> => {
      const params: any = { page, page_size: pageSize };
      if (status) params.status = status;
      if (query) params.query = query;
      const res = await api.get('/jiras', { params });
      const data = handleResponse<JiraSummary[]>(res);
      return { items: data, total: res.data.meta?.total || 0 };
    },
    get: async (jiraId: string): Promise<JiraDetail> => {
      const res = await api.get(`/jiras/${jiraId}`);
      return handleResponse<JiraDetail>(res);
    },
  },

  // Coverage
  coverage: {
    getSummary: async (): Promise<CoverageSummary> => {
      const res = await api.get('/coverage');
      return handleResponse<CoverageSummary>(res);
    },
    getMatrix: async (page = 1, pageSize = 50, status?: string): Promise<CoverageMatrix> => {
      const params: any = { page, page_size: pageSize };
      if (status) params.status = status;
      const res = await api.get('/coverage/matrix', { params });
      return handleResponse<CoverageMatrix>(res);
    },
    getMissing: async (): Promise<MissingMerge[]> => {
      const res = await api.get('/coverage/missing');
      return handleResponse<MissingMerge[]>(res);
    },
  },

  // Content Verification
  content: {
    getSummary: async (): Promise<{ total_files: number; identical_count: number; drifted_count: number; overall_drift_score: number }> => {
      const res = await api.get('/content/verification');
      return handleResponse<{ total_files: number; identical_count: number; drifted_count: number; overall_drift_score: number }>(res);
    },
    getDriftReport: async (): Promise<DriftReport> => {
      const res = await api.get('/content/drift');
      return handleResponse<DriftReport>(res);
    },
  },

  // Merge Delays
  delays: {
    getSummary: async (): Promise<DelayStatistics> => {
      const res = await api.get('/delays');
      return handleResponse<DelayStatistics>(res);
    },
    getRanking: async (): Promise<FolderDelayRank[]> => {
      const res = await api.get('/delays/ranking');
      // Wait, endpoint is `/delays/ranking` but delay.py schema lists folder_rankings under DelayStatistics.
      // Let's verify what the router app/api/v1/delays.py returns. We will handle envelope.
      return handleResponse<FolderDelayRank[]>(res);
    },
  },

  // Folder Health
  folders: {
    list: async (): Promise<FolderHealthResult[]> => {
      const res = await api.get('/folders');
      return handleResponse<FolderHealthResult[]>(res);
    },
    getRanking: async (): Promise<FolderHealthRank[]> => {
      const res = await api.get('/folders/ranking');
      return handleResponse<FolderHealthRank[]>(res);
    },
    getHeatmap: async (): Promise<HeatmapCell[]> => {
      const res = await api.get('/folders/heatmap');
      return handleResponse<HeatmapCell[]>(res);
    },
  },

  // Violations
  violations: {
    list: async (page = 1, pageSize = 50, severity?: string, category?: string, isAcknowledged?: boolean): Promise<{ items: RuleViolation[], total: number }> => {
      const params: any = { page, page_size: pageSize };
      if (severity) params.severity = severity;
      if (category) params.category = category;
      if (isAcknowledged !== undefined) params.is_acknowledged = isAcknowledged;
      const res = await api.get('/violations', { params });
      const data = handleResponse<RuleViolation[]>(res);
      return { items: data, total: res.data.meta?.total || 0 };
    },
    getSummary: async (): Promise<ViolationSummary> => {
      const res = await api.get('/violations/summary');
      return handleResponse<ViolationSummary>(res);
    },
    acknowledge: async (violationId: string, note?: string): Promise<void> => {
      await api.post(`/violations/${violationId}/acknowledge`, { acknowledge_note: note });
    },
    evaluate: async (): Promise<{ message: string; violations_count: number }> => {
      const res = await api.post('/violations/evaluate');
      return handleResponse<{ message: string; violations_count: number }>(res);
    },
  },

  // Trends
  trends: {
    getCoverage: async (period = '30d'): Promise<TrendPoint[]> => {
      const res = await api.get('/trends/coverage', { params: { period } });
      return handleResponse<TrendPoint[]>(res);
    },
    getHealth: async (folder?: string, period = '30d'): Promise<TrendPoint[]> => {
      const params: any = { period };
      if (folder) params.folder = folder;
      const res = await api.get('/trends/health', { params });
      return handleResponse<TrendPoint[]>(res);
    },
    getDelay: async (period = '30d'): Promise<TrendPoint[]> => {
      const res = await api.get('/trends/delay', { params: { period } });
      return handleResponse<TrendPoint[]>(res);
    },
    getViolations: async (period = '30d'): Promise<TrendPoint[]> => {
      const res = await api.get('/trends/violations', { params: { period } });
      return handleResponse<TrendPoint[]>(res);
    },
  },

  // Dashboard Aggregates
  dashboard: {
    getSummary: async (): Promise<DashboardSummary> => {
      const res = await api.get('/dashboard');
      return handleResponse<DashboardSummary>(res);
    },
    getKpis: async (): Promise<DashboardKPICards> => {
      const res = await api.get('/dashboard/kpis');
      return handleResponse<DashboardKPICards>(res);
    },
    getScore: async (): Promise<GovernanceScoreDetail> => {
      const res = await api.get('/dashboard/governance-score');
      return handleResponse<GovernanceScoreDetail>(res);
    },
  },

  // Reports
  reports: {
    generateExcel: async (repoId: string, config = {}): Promise<{ report_id: string; message: string }> => {
      const res = await api.post('/reports/excel', { repository_id: repoId, config });
      return handleResponse<{ report_id: string; message: string }>(res);
    },
    generatePdf: async (repoId: string, config = {}): Promise<{ report_id: string; message: string }> => {
      const res = await api.post('/reports/pdf', { repository_id: repoId, config });
      return handleResponse<{ report_id: string; message: string }>(res);
    },
    list: async (): Promise<any[]> => {
      const res = await api.get('/reports');
      return handleResponse<any[]>(res);
    },
    downloadUrl: (reportId: string): string => {
      return `${API_URL}/api/v1/reports/${reportId}/download`;
    },
  },
};
