import { useEffect, useState } from 'react';
import {
  AlertCircle,
  Check,
  CheckCircle2,
  Copy,
  ExternalLink,
  Github,
  Key,
  Layers,
  Link2,
  Loader2,
  Lock,
  RefreshCw,
  Server,
  Settings2,
  ShieldCheck,
  Trash2,
  Zap,
} from 'lucide-react';
import {
  connectGitHubAccount,
  disconnectGitHubAccount,
  fetchGitHubStatus,
} from '../../../api/client';
import { GitHubAccountStatus } from '../../../types';

export function SettingsView() {
  const [status, setStatus] = useState<GitHubAccountStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [tokenInput, setTokenInput] = useState('');
  const [accountType, setAccountType] = useState('pat');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [copiedWebhook, setCopiedWebhook] = useState(false);

  const loadStatus = async () => {
    setLoading(true);
    try {
      const data = await fetchGitHubStatus();
      setStatus(data);
    } catch {
      setStatus({ is_connected: false });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tokenInput.trim()) return;
    setIsSubmitting(true);
    setMessage(null);
    try {
      const updated = await connectGitHubAccount(tokenInput.trim(), accountType);
      setStatus(updated);
      setTokenInput('');
      setMessage({
        type: 'success',
        text: `Connected successfully as @${updated.username || 'GitHub User'}! Tokens are encrypted at rest with Fernet.`,
      });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to connect GitHub account' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect your GitHub account?')) return;
    setIsSubmitting(true);
    setMessage(null);
    try {
      await disconnectGitHubAccount();
      setStatus({ is_connected: false });
      setMessage({ type: 'success', text: 'GitHub account disconnected and encrypted token removed.' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to disconnect' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const webhookUrl = `${window.location.origin.replace(':5173', ':8000')}/api/v1/github/webhook`;

  const copyWebhookUrl = () => {
    navigator.clipboard.writeText(webhookUrl);
    setCopiedWebhook(true);
    setTimeout(() => setCopiedWebhook(false), 2000);
  };

  return (
    <div className="view-container">
      <section className="surface-card full-card">
        <div className="card-heading">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Settings2 size={20} color="var(--lime)" />
              <h3 style={{ margin: 0 }}>Integrations & Platform Settings</h3>
            </div>
            <p style={{ marginTop: '4px' }}>
              Configure GitHub credentials, automated PR Webhooks, and inspect engine deployment security.
            </p>
          </div>

          <button
            className="button button-ghost button-small"
            onClick={loadStatus}
            disabled={loading}
            type="button"
          >
            <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
          </button>
        </div>

        {message && (
          <div
            style={{
              margin: '16px 0',
              padding: '12px 16px',
              borderRadius: '8px',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              background:
                message.type === 'success'
                  ? 'rgba(199, 243, 107, 0.12)'
                  : 'rgba(239, 68, 68, 0.12)',
              border: `1px solid ${
                message.type === 'success' ? 'var(--lime)' : 'rgba(239, 68, 68, 0.3)'
              }`,
              color: message.type === 'success' ? 'var(--ws-text)' : '#ef4444',
            }}
          >
            {message.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
            <span>{message.text}</span>
          </div>
        )}

        {/* Section 1: GitHub Connection */}
        <div
          style={{
            background: 'var(--ws-surface-subtle)',
            border: '1px solid var(--ws-border)',
            borderRadius: '10px',
            padding: '20px 24px',
            margin: '20px 0',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Github size={22} color="var(--lime)" />
              <div>
                <b style={{ fontSize: '16px', color: 'var(--ws-text)' }}>GitHub Integration</b>
                <div style={{ fontSize: '12px', color: 'var(--ws-text-muted)' }}>
                  Enables importing private/public repositories, analyzing PR unified diffs, and posting executive comments.
                </div>
              </div>
            </div>

            {status?.is_connected ? (
              <span
                style={{
                  background: 'rgba(199, 243, 107, 0.15)',
                  color: 'var(--lime)',
                  padding: '4px 12px',
                  borderRadius: '16px',
                  fontSize: '12px',
                  fontWeight: 600,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <CheckCircle2 size={14} /> Connected
              </span>
            ) : (
              <span
                style={{
                  background: 'rgba(255, 255, 255, 0.08)',
                  color: 'var(--ws-text-muted)',
                  padding: '4px 12px',
                  borderRadius: '16px',
                  fontSize: '12px',
                }}
              >
                Not Connected
              </span>
            )}
          </div>

          {loading ? (
            <div style={{ padding: '20px 0', textAlign: 'center' }}>
              <Loader2 size={20} className="spin" />
            </div>
          ) : status?.is_connected ? (
            <div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                  gap: '14px',
                  background: 'rgba(255, 255, 255, 0.02)',
                  padding: '16px',
                  borderRadius: '8px',
                  border: '1px solid var(--ws-border)',
                  marginBottom: '16px',
                }}
              >
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--ws-text-muted)' }}>GitHub User</div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--ws-text)' }}>
                    @{status.username || 'Authorized User'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', color: 'var(--ws-text-muted)' }}>Token Storage</div>
                  <div style={{ fontSize: '14px', fontFamily: 'var(--font-mono)', color: 'var(--lime)' }}>
                    {status.masked_token || 'Encrypted (Fernet 256-bit)'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', color: 'var(--ws-text-muted)' }}>Scopes / Permissions</div>
                  <div style={{ fontSize: '13px', color: 'var(--ws-text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {status.scopes || 'repo, read:user'}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  className="button button-ghost button-small"
                  onClick={handleDisconnect}
                  disabled={isSubmitting}
                  style={{ color: '#ef4444' }}
                  type="button"
                >
                  <Trash2 size={14} /> Disconnect GitHub Account
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleConnect} style={{ display: 'grid', gap: '14px', maxWidth: '600px' }}>
              <div>
                <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                  Personal Access Token (classic or fine-grained)
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type="password"
                    className="text-input"
                    placeholder="ghp_••••••••••••••••••••••••••••••••••••"
                    value={tokenInput}
                    onChange={(e) => setTokenInput(e.target.value)}
                    required
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      background: 'var(--ws-surface)',
                      color: 'var(--ws-text)',
                      border: '1px solid var(--ws-border)',
                      borderRadius: '8px',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '13px',
                    }}
                  />
                </div>
                <div style={{ fontSize: '11px', color: 'var(--ws-text-muted)', marginTop: '4px' }}>
                  Required scopes: <code style={{ color: 'var(--lime)' }}>repo</code> (full repository access) and{' '}
                  <code style={{ color: 'var(--lime)' }}>read:user</code>. Tokens are encrypted using symmetric Fernet encryption before database storage.
                </div>
              </div>

              <div>
                <button
                  className="button button-lime button-small"
                  type="submit"
                  disabled={isSubmitting || !tokenInput.trim()}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 size={14} className="spin" /> Verifying Token...
                    </>
                  ) : (
                    <>
                      <Key size={14} /> Save & Encrypt GitHub Token
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Section 2: GitHub Webhooks Automation */}
        <div
          style={{
            background: 'var(--ws-surface-subtle)',
            border: '1px solid var(--ws-border)',
            borderRadius: '10px',
            padding: '20px 24px',
            margin: '20px 0',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            <Zap size={22} color="var(--lime)" />
            <b style={{ fontSize: '16px', color: 'var(--ws-text)' }}>Automated Pull Request Webhooks</b>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--ws-text-muted)', marginBottom: '16px' }}>
            Configure a webhook on your GitHub repository to automatically run ChangeRadar blast radius analysis on every opened or synchronized Pull Request.
          </p>

          <div style={{ display: 'grid', gap: '10px' }}>
            <div style={{ fontSize: '12px', color: 'var(--ws-text-muted)' }}>Payload URL</div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'rgba(255, 255, 255, 0.03)',
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid var(--ws-border)',
              }}
            >
              <code style={{ flex: 1, fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--lime)' }}>
                {webhookUrl}
              </code>
              <button
                className="button button-ghost button-small"
                onClick={copyWebhookUrl}
                type="button"
              >
                {copiedWebhook ? <Check size={14} /> : <Copy size={14} />} {copiedWebhook ? 'Copied' : 'Copy'}
              </button>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--ws-text-muted)' }}>
              ChangeRadar validates the <code>X-Hub-Signature-256</code> header and guarantees idempotency on duplicate deliveries via <code>X-GitHub-Delivery</code>.
            </div>
          </div>
        </div>

        {/* Section 3: Platform Architecture & Probes */}
        <div
          style={{
            background: 'var(--ws-surface-subtle)',
            border: '1px solid var(--ws-border)',
            borderRadius: '10px',
            padding: '20px 24px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            <Server size={22} color="var(--lime)" />
            <b style={{ fontSize: '16px', color: 'var(--ws-text)' }}>Platform Engine & Deployment Probes</b>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '14px',
              fontSize: '13px',
            }}
          >
            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '6px' }}>
              <div style={{ color: 'var(--ws-text-muted)', fontSize: '11px' }}>Analysis Engine Version</div>
              <b style={{ color: 'var(--ws-text)' }}>1.0.0 (Connected Release)</b>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '6px' }}>
              <div style={{ color: 'var(--ws-text-muted)', fontSize: '11px' }}>Background Worker</div>
              <b style={{ color: 'var(--lime)' }}>Active (Concurrency: 4)</b>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '6px' }}>
              <div style={{ color: 'var(--ws-text-muted)', fontSize: '11px' }}>Liveness Probe</div>
              <code style={{ color: 'var(--ws-text)' }}>GET /health (HTTP 200)</code>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '6px' }}>
              <div style={{ color: 'var(--ws-text-muted)', fontSize: '11px' }}>Readiness Probe</div>
              <code style={{ color: 'var(--ws-text)' }}>GET /ready (HTTP 200)</code>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
