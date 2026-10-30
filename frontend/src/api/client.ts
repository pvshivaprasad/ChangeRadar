import { SystemHealth } from '../types';

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
