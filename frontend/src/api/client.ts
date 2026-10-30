import {
  ImpactAnalysisReport,
  ScanSummary,
  SystemHealth,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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
  headCommit: string = 'HEAD'
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
