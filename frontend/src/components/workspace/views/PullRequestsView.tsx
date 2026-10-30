import { useEffect, useState } from 'react';
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  ExternalLink,
  GitBranch,
  Github,
  GitPullRequest,
  Loader2,
  MessageSquare,
  Play,
  RefreshCw,
  Send,
  ShieldAlert,
  Zap,
} from 'lucide-react';
import {
  analyzePullRequest,
  fetchPullRequests,
  publishPullRequestComment,
  setActiveAnalysisId,
} from '../../../api/client';
import {
  AnalysisRecord,
  GitHubPullRequest,
  ImpactAnalysisReport,
  PageId,
  RepositoryRecord,
} from '../../../types';
import { EmptyState } from '../../ui/EmptyState';

interface PullRequestsViewProps {
  repositories: RepositoryRecord[];
  onSelectReport: (report: ImpactAnalysisReport) => void;
  onNavigate: (page: PageId) => void;
}

export function PullRequestsView({
  repositories,
  onSelectReport,
  onNavigate,
}: PullRequestsViewProps) {
  const [selectedRepoId, setSelectedRepoId] = useState<number | null>(() => {
    return repositories.length > 0 ? repositories[0].id : null;
  });

  const [pullRequests, setPullRequests] = useState<GitHubPullRequest[]>([]);
  const [loading, setLoading] = useState(false);
  const [analyzingPr, setAnalyzingPr] = useState<number | null>(null);
  const [commentingPr, setCommentingPr] = useState<number | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Sync selected repository if list updates
  useEffect(() => {
    if (repositories.length > 0 && selectedRepoId === null) {
      setSelectedRepoId(repositories[0].id);
    }
  }, [repositories, selectedRepoId]);

  const loadPullRequests = async (repoId: number) => {
    setLoading(true);
    setMessage(null);
    try {
      const prs = await fetchPullRequests(repoId);
      setPullRequests(prs);
    } catch (err: any) {
      // If repository isn't a GitHub remote or user hasn't connected token
      setPullRequests([]);
      setMessage({
        type: 'error',
        text: err.message || 'Could not fetch pull requests. Ensure GitHub is connected in Settings.',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedRepoId) {
      loadPullRequests(selectedRepoId);
    }
  }, [selectedRepoId]);

  const handleAnalyze = async (prNumber: number) => {
    if (!selectedRepoId) return;
    setAnalyzingPr(prNumber);
    setMessage(null);
    try {
      const res = await analyzePullRequest(selectedRepoId, prNumber, false);
      if (res.report) {
        onSelectReport(res.report);
        if (res.analysis?.id) {
          setActiveAnalysisId(res.analysis.id);
        }
        setMessage({
          type: 'success',
          text: `Pull Request #${prNumber} impact analysis completed successfully! Risk: ${res.report.risk_level.toUpperCase()} (${res.report.risk_score}/100).`,
        });
        loadPullRequests(selectedRepoId);
      }
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Analysis failed' });
    } finally {
      setAnalyzingPr(null);
    }
  };

  const handlePostComment = async (prNumber: number) => {
    if (!selectedRepoId) return;
    setCommentingPr(prNumber);
    setMessage(null);
    try {
      const res = await publishPullRequestComment(selectedRepoId, prNumber);
      setMessage({
        type: 'success',
        text: `Published executive ChangeRadar analysis comment to GitHub PR #${prNumber} (Comment ID: ${res.comment_id}).`,
      });
      loadPullRequests(selectedRepoId);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to post GitHub comment' });
    } finally {
      setCommentingPr(null);
    }
  };

  return (
    <div className="view-container">
      <section className="surface-card full-card">
        <div className="card-heading">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <GitPullRequest size={20} color="var(--lime)" />
              <h3 style={{ margin: 0 }}>GitHub Pull Request Intelligence</h3>
            </div>
            <p style={{ marginTop: '4px' }}>
              Deterministic AST blast radius analysis, downstream caller tracing, and idempotent executive PR comments.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {repositories.length > 0 && (
              <select
                className="select-input"
                value={selectedRepoId || ''}
                onChange={(e) => setSelectedRepoId(Number(e.target.value))}
                style={{
                  background: 'var(--ws-surface-subtle)',
                  color: 'var(--ws-text)',
                  border: '1px solid var(--ws-border)',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  fontSize: '13px',
                }}
              >
                {repositories.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name} ({r.default_branch})
                  </option>
                ))}
              </select>
            )}

            <button
              className="button button-ghost button-small"
              onClick={() => selectedRepoId && loadPullRequests(selectedRepoId)}
              disabled={loading || !selectedRepoId}
              type="button"
            >
              <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
            </button>
          </div>
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

        {loading ? (
          <div style={{ padding: '60px 0', textAlign: 'center', color: 'var(--ws-text-muted)' }}>
            <Loader2 size={28} className="spin" style={{ margin: '0 auto 12px' }} />
            <p>Scanning pull requests from GitHub...</p>
          </div>
        ) : pullRequests.length === 0 ? (
          <div style={{ margin: '24px 0' }}>
            <EmptyState
              icon={<GitPullRequest size={24} />}
              title="No active Pull Requests found"
              description="Connect your GitHub account or repository in Settings to review pull requests, detect structural change blast radiuses, and publish PR comments."
              action="Configure GitHub Integration"
              onAction={() => onNavigate('settings')}
            />
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '14px', margin: '20px 0' }}>
            {pullRequests.map((pr) => {
              const hasAnalysis = !!pr.latest_analysis;
              const isWorking = analyzingPr === pr.number || commentingPr === pr.number;

              return (
                <div
                  key={pr.number}
                  style={{
                    background: 'var(--ws-surface-subtle)',
                    border: '1px solid var(--ws-border)',
                    borderRadius: '10px',
                    padding: '18px 20px',
                    display: 'flex',
                    flexWrap: 'wrap',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: '16px',
                  }}
                >
                  <div style={{ flex: '1 1 360px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                      <span
                        style={{
                          fontFamily: 'var(--font-mono)',
                          fontWeight: 700,
                          color: 'var(--lime)',
                          fontSize: '14px',
                        }}
                      >
                        #{pr.number}
                      </span>
                      <b style={{ fontSize: '15px', color: 'var(--ws-text)' }}>{pr.title}</b>
                      {pr.html_url && (
                        <a
                          href={pr.html_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ color: 'var(--ws-text-muted)', display: 'inline-flex' }}
                        >
                          <ExternalLink size={13} />
                        </a>
                      )}
                    </div>

                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        fontSize: '12px',
                        color: 'var(--ws-text-muted)',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      <span>
                        <GitBranch size={12} style={{ display: 'inline', marginRight: '4px' }} />
                        {pr.base_ref} ➔ {pr.head_ref}
                      </span>
                      <span>•</span>
                      <span>by @{pr.author}</span>
                      {hasAnalysis && (
                        <>
                          <span>•</span>
                          <span
                            style={{
                              background:
                                pr.latest_analysis?.risk_level === 'high'
                                  ? 'rgba(239, 68, 68, 0.15)'
                                  : pr.latest_analysis?.risk_level === 'elevated'
                                  ? 'rgba(245, 158, 11, 0.15)'
                                  : 'rgba(199, 243, 107, 0.15)',
                              color:
                                pr.latest_analysis?.risk_level === 'high'
                                  ? '#ef4444'
                                  : pr.latest_analysis?.risk_level === 'elevated'
                                  ? '#f59e0b'
                                  : 'var(--lime)',
                              padding: '2px 8px',
                              borderRadius: '4px',
                              fontWeight: 700,
                              textTransform: 'uppercase',
                            }}
                          >
                            Risk: {pr.latest_analysis?.risk_level} ({pr.latest_analysis?.risk_score}/100)
                          </span>
                        </>
                      )}
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <button
                      className="button button-lime button-small"
                      onClick={() => handleAnalyze(pr.number)}
                      disabled={isWorking}
                      type="button"
                    >
                      {analyzingPr === pr.number ? (
                        <>
                          <Loader2 size={14} className="spin" /> Analyzing...
                        </>
                      ) : (
                        <>
                          <Zap size={14} /> {hasAnalysis ? 'Re-analyze' : 'Analyze Impact'}
                        </>
                      )}
                    </button>

                    {hasAnalysis && (
                      <button
                        className="button button-ghost button-small"
                        onClick={() => handlePostComment(pr.number)}
                        disabled={isWorking}
                        title="Post executive summary comment to GitHub PR"
                        type="button"
                      >
                        {commentingPr === pr.number ? (
                          <>
                            <Loader2 size={14} className="spin" /> Posting...
                          </>
                        ) : (
                          <>
                            <Send size={14} /> Comment on PR
                          </>
                        )}
                      </button>
                    )}

                    {hasAnalysis && pr.latest_analysis?.report && (
                      <button
                        className="button button-ghost button-small"
                        onClick={() => {
                          if (pr.latest_analysis?.report) {
                            onSelectReport(pr.latest_analysis.report);
                            setActiveAnalysisId(pr.latest_analysis.id);
                            onNavigate('analysis');
                          }
                        }}
                        type="button"
                      >
                        View Map <ArrowRight size={14} />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
