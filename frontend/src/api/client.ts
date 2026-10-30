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
const USER_KEY = 'changeradar_cached_user';
const ACTIVE_ANALYSIS_KEY = 'changeradar_active_analysis_id';

// ---------------------------------------------------------------------------
// Session & Cache Helpers
// ---------------------------------------------------------------------------

let inMemorySessionToken: string | null = null;

export function getAuthToken(): string | null {
  return inMemorySessionToken || localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token: string, remember: boolean = true): void {
  inMemorySessionToken = token;
  // Security best practice: Rely on HttpOnly cookie for persistent browser storage
  // to eliminate XSS token exfiltration risks.
  localStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
}

export function clearAuthToken(): void {
  inMemorySessionToken = null;
  localStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
}

export function getCachedUser(): User | null {
  try {
    const raw = localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setCachedUser(user: User, remember: boolean = true): void {
  const serialized = JSON.stringify(user);
  if (remember) {
    localStorage.setItem(USER_KEY, serialized);
    sessionStorage.removeItem(USER_KEY);
  } else {
    sessionStorage.setItem(USER_KEY, serialized);
    localStorage.removeItem(USER_KEY);
  }
}

export function clearCachedUser(): void {
  localStorage.removeItem(USER_KEY);
  sessionStorage.removeItem(USER_KEY);
}

export function getActiveAnalysisId(): number | null {
  const val = sessionStorage.getItem(ACTIVE_ANALYSIS_KEY) || localStorage.getItem(ACTIVE_ANALYSIS_KEY);
  return val ? parseInt(val, 10) : null;
}

export function setActiveAnalysisId(id: number | null): void {
  if (id === null) {
    sessionStorage.removeItem(ACTIVE_ANALYSIS_KEY);
    localStorage.removeItem(ACTIVE_ANALYSIS_KEY);
  } else {
    sessionStorage.setItem(ACTIVE_ANALYSIS_KEY, id.toString());
    localStorage.setItem(ACTIVE_ANALYSIS_KEY, id.toString());
  }
}

export function clearActiveAnalysisId(): void {
  sessionStorage.removeItem(ACTIVE_ANALYSIS_KEY);
  localStorage.removeItem(ACTIVE_ANALYSIS_KEY);
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
      credentials: 'include',
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
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Login failed. Please check your credentials.');
  }
  const session: AuthSession = await res.json();
  setAuthToken(session.token, true);
  setCachedUser(session.user, true);
  return session;
}

export async function registerUser(name: string, email: string, password: string): Promise<AuthSession> {
  const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ name, email, password }),
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Registration failed.');
  }
  const session: AuthSession = await res.json();
  setAuthToken(session.token, true);
  setCachedUser(session.user, true);
  return session;
}

export async function logoutUser(): Promise<void> {
  try {
    await fetch(`${API_BASE}/api/v1/auth/logout`, {
      method: 'POST',
      headers: authHeaders(),
      credentials: 'include',
    });
  } catch {
    // Continue local cleanup even if server is offline
  } finally {
    clearAuthToken();
    clearCachedUser();
    clearActiveAnalysisId();
  }
}

export async function fetchCurrentUser(): Promise<User | null> {
  const token = getAuthToken();
  // If no token in storage, check if cookie works with /auth/me
  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/me`, {
      headers: authHeaders(),
      credentials: 'include',
    });
    if (!res.ok) {
      if (res.status === 401) {
        clearAuthToken();
        clearCachedUser();
      }
      return null;
    }
    const user: User = await res.json();
    setCachedUser(user, true);
    return user;
  } catch {
    // Return cached user if offline temporarily
    return getCachedUser();
  }
}

// ---------------------------------------------------------------------------
// Repositories & Analyses Persistence
// ---------------------------------------------------------------------------

export async function fetchRepositories(): Promise<RepositoryRecord[]> {
  const res = await fetch(`${API_BASE}/api/v1/repositories`, {
    headers: authHeaders(),
    credentials: 'include',
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
    credentials: 'include',
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
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to delete repository.');
  }
}

export async function fetchRepositoryAnalyses(id: number): Promise<AnalysisRecord[]> {
  const res = await fetch(`${API_BASE}/api/v1/repositories/${id}/analyses`, {
    headers: authHeaders(),
    credentials: 'include',
  });
  if (!res.ok) {
    return [];
  }
  return res.json();
}

export async function fetchAllAnalyses(): Promise<AnalysisRecord[]> {
  const res = await fetch(`${API_BASE}/api/v1/analyses`, {
    headers: authHeaders(),
    credentials: 'include',
  });
  if (!res.ok) {
    return [];
  }
  return res.json();
}

export async function fetchAnalysisById(id: number): Promise<AnalysisRecord | null> {
  const res = await fetch(`${API_BASE}/api/v1/analyses/${id}`, {
    headers: authHeaders(),
    credentials: 'include',
  });
  if (!res.ok) {
    return null;
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
    credentials: 'include',
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
    headers: authHeaders(),
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Analysis failed with status ${res.status}`);
  }
  return res.json();
}

export async function fetchSampleScan(): Promise<ScanSummary> {
  const res = await fetch(`${API_BASE}/api/v1/sample/scan`, {
    headers: authHeaders(),
    credentials: 'include',
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
    headers: authHeaders(),
    body: JSON.stringify({
      repo_path: repoPath,
      base_commit: baseCommit,
      head_commit: headCommit,
    }),
    credentials: 'include',
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
    headers: authHeaders(),
    body: JSON.stringify({ repo_path: repoPath }),
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Scan failed: ${res.statusText}`);
  }
  return res.json();
}
