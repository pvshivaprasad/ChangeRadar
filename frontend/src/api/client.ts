import {
  AnalysisRecord,
  AuthSession,
  ImpactAnalysisReport,
  RepositoryRecord,
  ScanSummary,
  SystemHealth,
  User,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const TOKEN_KEY = 'changeradar_session_token';

export function getAuthToken(): string | null {
  return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token: string, remember: boolean = true): void {
  if (remember) {
    localStorage.setItem(TOKEN_KEY, token);
    sessionStorage.removeItem(TOKEN_KEY);
  } else {
    sessionStorage.setItem(TOKEN_KEY, token);
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function clearAuthToken(): void {
  localStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
}

function authHeaders(): Record<string, string> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export async function fetchSystemHealth(): Promise<SystemHealth> {
  const startTime = performance.now();
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 4000);

    const res = await fetch(`${API_BASE}/health`, {
      signal: controller.signal,
      headers: { Accept: 'application/json' },
    });
    clearTimeout(timeoutId);

    const duration = Math.round(performance.now() - startTime);

    if (!res.ok) {
      return {
        status: 'degraded',
        service: 'changeradar-api',
        version: '0.1.1',
        environment: 'development',
        database: { connected: false, dialect: 'unknown', error: `HTTP ${res.status}` },
        responseTimeMs: duration,
      };
    }

    const data = await res.json();
    return {
      ...data,
      responseTimeMs: duration,
    };
  } catch (err: unknown) {
    const duration = Math.round(performance.now() - startTime);
    const errorMessage = err instanceof Error ? err.message : 'Connection refused';
    return {
      status: 'offline',
      service: 'changeradar-api',
      version: '0.1.1',
      environment: 'offline',
      database: { connected: false, dialect: 'offline', error: errorMessage },
      responseTimeMs: duration,
    };
  }
}

// ---------------------------------------------------------------------------
// Authentication
// ---------------------------------------------------------------------------

export async function loginUser(email: string, password: string): Promise<AuthSession> {
  const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Login failed. Please check your credentials.');
  }
  return res.json();
}

export async function registerUser(name: string, email: string, password: string): Promise<AuthSession> {
  const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ name, email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Registration failed.');
  }
  return res.json();
}

export async function fetchCurrentUser(): Promise<User | null> {
  const token = getAuthToken();
  if (!token) return null;

  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/me`, {
      headers: authHeaders(),
    });
    if (!res.ok) {
      clearAuthToken();
      return null;
    }
    return res.json();
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Repositories & Analyses Persistence
// ---------------------------------------------------------------------------

export async function fetchRepositories(): Promise<RepositoryRecord[]> {
  const res = await fetch(`${API_BASE}/api/v1/repositories`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    return [];
  }
  return res.json();
}

export async function createRepository(
  path: string,
  name?: string,
  defaultBranch: string = 'main',
): Promise<RepositoryRecord> {
  const res = await fetch(`${API_BASE}/api/v1/repositories`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ path, name, default_branch: defaultBranch }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to import repository.');
  }
  return res.json();
}

export async function deleteRepository(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/repositories/${id}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to delete repository.');
  }
}

export async function fetchRepositoryAnalyses(id: number): Promise<AnalysisRecord[]> {
  const res = await fetch(`${API_BASE}/api/v1/repositories/${id}/analyses`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    return [];
  }
  return res.json();
}

export async function fetchAllAnalyses(): Promise<AnalysisRecord[]> {
  const res = await fetch(`${API_BASE}/api/v1/analyses`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    return [];
  }
  return res.json();
}

export async function analyzePersistedRepository(
  id: number,
  baseCommit: string = 'HEAD~1',
  headCommit: string = 'HEAD',
): Promise<AnalysisRecord> {
  const res = await fetch(`${API_BASE}/api/v1/repositories/${id}/analyze`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ base_commit: baseCommit, head_commit: headCommit }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Analysis failed.');
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Direct Scan & Sample Endpoints
// ---------------------------------------------------------------------------

export async function fetchSampleAnalysis(): Promise<ImpactAnalysisReport> {
  const res = await fetch(`${API_BASE}/api/v1/sample/run`, {
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Analysis failed with status ${res.status}`);
  }
  return res.json();
}

export async function fetchSampleScan(): Promise<ScanSummary> {
  const res = await fetch(`${API_BASE}/api/v1/sample/scan`, {
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Scan failed with status ${res.status}`);
  }
  return res.json();
}

export async function analyzeRepository(
  repoPath: string,
  baseCommit: string = 'HEAD~1',
  headCommit: string = 'HEAD',
): Promise<ImpactAnalysisReport> {
  const res = await fetch(`${API_BASE}/api/v1/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({
      repo_path: repoPath,
      base_commit: baseCommit,
      head_commit: headCommit,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Analysis failed: ${res.statusText}`);
  }
  return res.json();
}

export async function scanRepository(repoPath: string): Promise<ScanSummary> {
  const res = await fetch(`${API_BASE}/api/v1/scan`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({ repo_path: repoPath }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Scan failed: ${res.statusText}`);
  }
  return res.json();
}
