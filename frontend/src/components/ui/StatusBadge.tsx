import { useEffect, useState } from 'react';
import { fetchSystemHealth } from '../../api/client';
import { SystemHealth } from '../../types';

export function StatusBadge({ minimal = false }: { minimal?: boolean }) {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const check = async () => {
      const res = await fetchSystemHealth();
      if (mounted) {
        setHealth(res);
        setLoading(false);
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  if (loading) {
    return (
      <span className="status-badge status-loading" title="Connecting to backend...">
        <span className="status-indicator-dot dot-loading" />
        {!minimal && <span>Connecting...</span>}
      </span>
    );
  }

  const isHealthy = health?.status === 'healthy';
  const isDegraded = health?.status === 'degraded';

  const dotClass = isHealthy ? 'dot-healthy' : isDegraded ? 'dot-degraded' : 'dot-offline';
  const label = isHealthy
    ? 'All systems operational'
    : isDegraded
      ? `Degraded (${health?.database.dialect})`
      : 'API Offline (Local mode)';

  const tooltip = health
    ? `Backend: ${health.service} v${health.version} | DB: ${health.database.dialect} (${
        health.database.connected ? 'connected' : health.database.error || 'disconnected'
      }) | Latency: ${health.responseTimeMs ?? 0}ms`
    : 'Backend status unknown';

  return (
    <span className={`status-badge status-${health?.status}`} title={tooltip}>
      <span className={`status-indicator-dot ${dotClass}`} />
      {!minimal && <span>{label}</span>}
      {!minimal && health?.responseTimeMs !== undefined && (
        <span className="status-latency">{health.responseTimeMs}ms</span>
      )}
    </span>
  );
}
