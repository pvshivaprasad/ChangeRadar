import { useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle,
  Clock,
  Compass,
  FileCode,
  Flame,
  GitCommit,
  History,
  Layers,
  Loader2,
  RefreshCw,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import {
  compareHistoricalAnalyses,
  fetchHistoricalPatterns,
} from '../../../api/client';
import {
  AnalysisRecord,
  HistoricalComparisonResult,
  HistoricalPatternsReport,
  RepositoryRecord,
} from '../../../types';
import { EmptyState } from '../../ui/EmptyState';

interface HistoricalIntelligenceViewProps {
  repositories: RepositoryRecord[];
  analyses: AnalysisRecord[];
}

export function HistoricalIntelligenceView({
  repositories,
  analyses,
}: HistoricalIntelligenceViewProps) {
  const [selectedRepoId, setSelectedRepoId] = useState<number | null>(() => {
    return repositories.length > 0 ? repositories[0].id : null;
  });

  const [patterns, setPatterns] = useState<HistoricalPatternsReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'hotspots' | 'paths' | 'tests' | 'compare'>('hotspots');

  // Comparative Diff States
  const [analysisIdA, setAnalysisIdA] = useState<number | null>(null);
  const [analysisIdB, setAnalysisIdB] = useState<number | null>(null);
  const [comparison, setComparison] = useState<HistoricalComparisonResult | null>(null);
  const [comparing, setComparing] = useState(false);
  const [compareError, setCompareError] = useState<string | null>(null);

  useEffect(() => {
    if (repositories.length > 0 && selectedRepoId === null) {
      setSelectedRepoId(repositories[0].id);
    }
  }, [repositories, selectedRepoId]);

  const loadPatterns = async (repoId: number) => {
    setLoading(true);
    try {
      const data = await fetchHistoricalPatterns(repoId);
      setPatterns(data);

      // Auto-set comparison candidates if analyses exist
      const repoAnalyses = analyses.filter((a) => a.repository_id === repoId && a.status === 'completed');
      if (repoAnalyses.length >= 2) {
        setAnalysisIdA(repoAnalyses[1].id);
        setAnalysisIdB(repoAnalyses[0].id);
      } else if (repoAnalyses.length === 1) {
        setAnalysisIdA(repoAnalyses[0].id);
        setAnalysisIdB(repoAnalyses[0].id);
      }
    } catch {
      setPatterns(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedRepoId) {
      loadPatterns(selectedRepoId);
    }
  }, [selectedRepoId]);

  const handleRunComparison = async () => {
    if (!selectedRepoId || !analysisIdA || !analysisIdB) return;
    setComparing(true);
    setCompareError(null);
    try {
      const res = await compareHistoricalAnalyses(selectedRepoId, analysisIdA, analysisIdB);
      setComparison(res);
    } catch (err: any) {
      setCompareError(err.message || 'Comparison failed');
    } finally {
      setComparing(false);
    }
  };

  const completedRepoAnalyses = analyses.filter(
    (a) => a.repository_id === selectedRepoId && a.status === 'completed',
  );

  return (
    <div className="view-container">
      <section className="surface-card full-card">
        <div className="card-heading">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <History size={20} color="var(--lime)" />
              <h3 style={{ margin: 0 }}>Historical Change Intelligence</h3>
            </div>
            <p style={{ marginTop: '4px' }}>
              Empirical change pattern intelligence derived strictly from persisted analysis records.
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
                    {r.name}
                  </option>
                ))}
              </select>
            )}

            <button
              className="button button-ghost button-small"
              onClick={() => selectedRepoId && loadPatterns(selectedRepoId)}
              disabled={loading || !selectedRepoId}
              type="button"
            >
              <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
            </button>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '60px 0', textAlign: 'center', color: 'var(--ws-text-muted)' }}>
            <Loader2 size={28} className="spin" style={{ margin: '0 auto 12px' }} />
            <p>Aggregating historical change patterns...</p>
          </div>
        ) : !patterns || patterns.total_analyses === 0 ? (
          <div style={{ margin: '24px 0' }}>
            <EmptyState
              icon={<History size={24} />}
              title="Insufficient Historical Analyses"
              description="Historical pattern detection requires completed analyses. Run change impact analyses on this repository to surface architectural hotspots and recurring paths."
            />
          </div>
        ) : (
          <>
            {/* Top Stat Cards */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '16px',
                margin: '20px 0',
              }}
            >
              <div
                style={{
                  background: 'var(--ws-surface-subtle)',
                  padding: '16px 20px',
                  borderRadius: '10px',
                  border: '1px solid var(--ws-border)',
                }}
              >
                <div style={{ fontSize: '12px', color: 'var(--ws-text-muted)', marginBottom: '4px' }}>
                  Analyzed Changes
                </div>
                <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--ws-text)' }}>
                  {patterns.total_analyses}
                </div>
              </div>

              <div
                style={{
                  background: 'var(--ws-surface-subtle)',
                  padding: '16px 20px',
                  borderRadius: '10px',
                  border: '1px solid var(--ws-border)',
                }}
              >
                <div style={{ fontSize: '12px', color: 'var(--ws-text-muted)', marginBottom: '4px' }}>
                  High-Risk Hotspots
                </div>
                <div style={{ fontSize: '24px', fontWeight: 700, color: '#f59e0b' }}>
                  {patterns.hotspots.length}
                </div>
              </div>

              <div
                style={{
                  background: 'var(--ws-surface-subtle)',
                  padding: '16px 20px',
                  borderRadius: '10px',
                  border: '1px solid var(--ws-border)',
                }}
              >
                <div style={{ fontSize: '12px', color: 'var(--ws-text-muted)', marginBottom: '4px' }}>
                  Recurring Paths
                </div>
                <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--lime)' }}>
                  {patterns.recurring_paths.length}
                </div>
              </div>

              <div
                style={{
                  background: 'var(--ws-surface-subtle)',
                  padding: '16px 20px',
                  borderRadius: '10px',
                  border: '1px solid var(--ws-border)',
                }}
              >
                <div style={{ fontSize: '12px', color: 'var(--ws-text-muted)', marginBottom: '4px' }}>
                  Recommended Tests
                </div>
                <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--ws-text)' }}>
                  {patterns.repeatedly_recommended_tests.length}
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div
              style={{
                display: 'flex',
                gap: '8px',
                borderBottom: '1px solid var(--ws-border)',
                marginBottom: '20px',
              }}
            >
              <button
                className={`button button-small ${activeTab === 'hotspots' ? 'button-lime' : 'button-ghost'}`}
                onClick={() => setActiveTab('hotspots')}
                type="button"
              >
                <Flame size={14} /> Hotspots & Modules
              </button>
              <button
                className={`button button-small ${activeTab === 'paths' ? 'button-lime' : 'button-ghost'}`}
                onClick={() => setActiveTab('paths')}
                type="button"
              >
                <Compass size={14} /> Recurring Paths ({patterns.recurring_paths.length})
              </button>
              <button
                className={`button button-small ${activeTab === 'tests' ? 'button-lime' : 'button-ghost'}`}
                onClick={() => setActiveTab('tests')}
                type="button"
              >
                <CheckCircle size={14} /> Test Drift ({patterns.repeatedly_recommended_tests.length})
              </button>
              <button
                className={`button button-small ${activeTab === 'compare' ? 'button-lime' : 'button-ghost'}`}
                onClick={() => setActiveTab('compare')}
                type="button"
              >
                <Layers size={14} /> Comparative Intelligence
              </button>
            </div>

            {/* Tab: Hotspots */}
            {activeTab === 'hotspots' && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                <div
                  style={{
                    background: 'var(--ws-surface-subtle)',
                    padding: '18px 20px',
                    borderRadius: '10px',
                    border: '1px solid var(--ws-border)',
                  }}
                >
                  <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: 'var(--ws-text)' }}>
                    🔥 Architectural Hotspots (High Blast Radius)
                  </h4>
                  <p style={{ fontSize: '12px', color: 'var(--ws-text-muted)', marginBottom: '14px' }}>
                    Modules whose modification repeatedly causes elevated or high structural risk.
                  </p>

                  {patterns.hotspots.length === 0 ? (
                    <div style={{ fontSize: '13px', color: 'var(--ws-text-muted)' }}>
                      No recurring high-risk hotspots detected.
                    </div>
                  ) : (
                    <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr style={{ color: 'var(--ws-text-muted)', textAlign: 'left', borderBottom: '1px solid var(--ws-border)' }}>
                          <th style={{ padding: '8px 0' }}>Module</th>
                          <th style={{ padding: '8px 0', textAlign: 'right' }}>High-Risk Changes</th>
                        </tr>
                      </thead>
                      <tbody>
                        {patterns.hotspots.map((h, i) => (
                          <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                            <td style={{ padding: '10px 0', fontFamily: 'var(--font-mono)', color: '#f59e0b' }}>
                              {h.file_path}
                            </td>
                            <td style={{ padding: '10px 0', textAlign: 'right', fontWeight: 600 }}>
                              {h.high_risk_occurrences} / {h.total_changes}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>

                <div
                  style={{
                    background: 'var(--ws-surface-subtle)',
                    padding: '18px 20px',
                    borderRadius: '10px',
                    border: '1px solid var(--ws-border)',
                  }}
                >
                  <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: 'var(--ws-text)' }}>
                    📦 Frequently Modified Modules
                  </h4>
                  <p style={{ fontSize: '12px', color: 'var(--ws-text-muted)', marginBottom: '14px' }}>
                    Files that evolve frequently across historical analysis records.
                  </p>

                  <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ color: 'var(--ws-text-muted)', textAlign: 'left', borderBottom: '1px solid var(--ws-border)' }}>
                        <th style={{ padding: '8px 0' }}>File Path</th>
                        <th style={{ padding: '8px 0', textAlign: 'right' }}>Frequency</th>
                      </tr>
                    </thead>
                    <tbody>
                      {patterns.frequently_modified_modules.map((m, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                          <td style={{ padding: '10px 0', fontFamily: 'var(--font-mono)' }}>{m.file_path}</td>
                          <td style={{ padding: '10px 0', textAlign: 'right', fontWeight: 600 }}>
                            {m.change_count} ({m.percentage}%)
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Tab: Recurring Paths */}
            {activeTab === 'paths' && (
              <div
                style={{
                  background: 'var(--ws-surface-subtle)',
                  padding: '18px 20px',
                  borderRadius: '10px',
                  border: '1px solid var(--ws-border)',
                }}
              >
                <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: 'var(--ws-text)' }}>
                  🧭 Recurring Call-Graph Blast Radius Paths
                </h4>
                <p style={{ fontSize: '12px', color: 'var(--ws-text-muted)', marginBottom: '16px' }}>
                  Downstream dependency propagation paths frequently traversed across changes.
                </p>

                {patterns.recurring_paths.length === 0 ? (
                  <div style={{ fontSize: '13px', color: 'var(--ws-text-muted)' }}>
                    No multi-hop propagation paths detected yet.
                  </div>
                ) : (
                  <div style={{ display: 'grid', gap: '10px' }}>
                    {patterns.recurring_paths.map((p, i) => (
                      <div
                        key={i}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '10px 14px',
                          background: 'rgba(255, 255, 255, 0.03)',
                          borderRadius: '6px',
                          border: '1px solid var(--ws-border)',
                          fontFamily: 'var(--font-mono)',
                          fontSize: '13px',
                        }}
                      >
                        <span style={{ color: 'var(--ws-text)' }}>{p.path}</span>
                        <span
                          style={{
                            background: 'rgba(199, 243, 107, 0.15)',
                            color: 'var(--lime)',
                            padding: '2px 8px',
                            borderRadius: '12px',
                            fontWeight: 700,
                            fontSize: '12px',
                          }}
                        >
                          {p.frequency}x recurring
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Tab: Tests */}
            {activeTab === 'tests' && (
              <div
                style={{
                  background: 'var(--ws-surface-subtle)',
                  padding: '18px 20px',
                  borderRadius: '10px',
                  border: '1px solid var(--ws-border)',
                }}
              >
                <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: 'var(--ws-text)' }}>
                  🧪 Repeatedly Recommended Tests
                </h4>
                <p style={{ fontSize: '12px', color: 'var(--ws-text-muted)', marginBottom: '16px' }}>
                  Targeted test cases recommended persistently across independent code changes.
                </p>

                <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ color: 'var(--ws-text-muted)', textAlign: 'left', borderBottom: '1px solid var(--ws-border)' }}>
                      <th style={{ padding: '8px 0' }}>Test Identifier</th>
                      <th style={{ padding: '8px 0', textAlign: 'right' }}>Recommendations</th>
                    </tr>
                  </thead>
                  <tbody>
                    {patterns.repeatedly_recommended_tests.map((t, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                        <td style={{ padding: '10px 0', fontFamily: 'var(--font-mono)', color: 'var(--lime)' }}>
                          {t.test}
                        </td>
                        <td style={{ padding: '10px 0', textAlign: 'right', fontWeight: 600 }}>
                          {t.recommendation_count} ({t.percentage}%)
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Tab: Comparative Diff */}
            {activeTab === 'compare' && (
              <div
                style={{
                  background: 'var(--ws-surface-subtle)',
                  padding: '18px 20px',
                  borderRadius: '10px',
                  border: '1px solid var(--ws-border)',
                }}
              >
                <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: 'var(--ws-text)' }}>
                  ⚖️ Analysis Comparative Intelligence
                </h4>
                <p style={{ fontSize: '12px', color: 'var(--ws-text-muted)', marginBottom: '16px' }}>
                  Compare two historical analysis snapshots to detect blast radius growth, risk delta, and test drift.
                </p>

                {completedRepoAnalyses.length < 2 ? (
                  <div style={{ color: 'var(--ws-text-muted)', fontSize: '13px' }}>
                    At least two completed analysis snapshots are required to perform a comparative diff.
                  </div>
                ) : (
                  <>
                    <div style={{ display: 'flex', gap: '16px', alignItems: 'center', marginBottom: '16px' }}>
                      <div style={{ flex: 1 }}>
                        <label style={{ fontSize: '12px', color: 'var(--ws-text-muted)', display: 'block', marginBottom: '4px' }}>
                          Base Snapshot (A)
                        </label>
                        <select
                          className="select-input"
                          value={analysisIdA || ''}
                          onChange={(e) => setAnalysisIdA(Number(e.target.value))}
                          style={{
                            width: '100%',
                            background: 'var(--ws-surface)',
                            color: 'var(--ws-text)',
                            border: '1px solid var(--ws-border)',
                            padding: '8px 12px',
                            borderRadius: '6px',
                          }}
                        >
                          {completedRepoAnalyses.map((a) => (
                            <option key={a.id} value={a.id}>
                              Analysis #{a.id} ({a.head_commit.slice(0, 7)}) — Risk: {a.risk_level.toUpperCase()} ({a.risk_score})
                            </option>
                          ))}
                        </select>
                      </div>

                      <div style={{ paddingTop: '20px' }}>➔</div>

                      <div style={{ flex: 1 }}>
                        <label style={{ fontSize: '12px', color: 'var(--ws-text-muted)', display: 'block', marginBottom: '4px' }}>
                          Target Snapshot (B)
                        </label>
                        <select
                          className="select-input"
                          value={analysisIdB || ''}
                          onChange={(e) => setAnalysisIdB(Number(e.target.value))}
                          style={{
                            width: '100%',
                            background: 'var(--ws-surface)',
                            color: 'var(--ws-text)',
                            border: '1px solid var(--ws-border)',
                            padding: '8px 12px',
                            borderRadius: '6px',
                          }}
                        >
                          {completedRepoAnalyses.map((a) => (
                            <option key={a.id} value={a.id}>
                              Analysis #{a.id} ({a.head_commit.slice(0, 7)}) — Risk: {a.risk_level.toUpperCase()} ({a.risk_score})
                            </option>
                          ))}
                        </select>
                      </div>

                      <button
                        className="button button-lime button-small"
                        onClick={handleRunComparison}
                        disabled={comparing || !analysisIdA || !analysisIdB}
                        style={{ marginTop: '20px' }}
                        type="button"
                      >
                        {comparing ? <Loader2 size={14} className="spin" /> : 'Compare Snapshots'}
                      </button>
                    </div>

                    {compareError && (
                      <div style={{ color: '#ef4444', fontSize: '13px', margin: '10px 0' }}>{compareError}</div>
                    )}

                    {comparison && (
                      <div style={{ marginTop: '20px', borderTop: '1px solid var(--ws-border)', paddingTop: '16px' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', marginBottom: '16px' }}>
                          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '8px' }}>
                            <div style={{ fontSize: '12px', color: 'var(--ws-text-muted)' }}>Risk Score Delta</div>
                            <div
                              style={{
                                fontSize: '20px',
                                fontWeight: 700,
                                color: comparison.risk_score_delta > 0 ? '#ef4444' : 'var(--lime)',
                              }}
                            >
                              {comparison.risk_score_delta > 0 ? `+${comparison.risk_score_delta}` : comparison.risk_score_delta}
                            </div>
                          </div>

                          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '8px' }}>
                            <div style={{ fontSize: '12px', color: 'var(--ws-text-muted)' }}>Impacted Count Delta</div>
                            <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--ws-text)' }}>
                              {comparison.impacted_count_delta > 0 ? `+${comparison.impacted_count_delta}` : comparison.impacted_count_delta}
                            </div>
                          </div>

                          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '8px' }}>
                            <div style={{ fontSize: '12px', color: 'var(--ws-text-muted)' }}>Newly Impacted</div>
                            <div style={{ fontSize: '20px', fontWeight: 700, color: '#f59e0b' }}>
                              {comparison.newly_impacted_symbols.length}
                            </div>
                          </div>

                          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '8px' }}>
                            <div style={{ fontSize: '12px', color: 'var(--ws-text-muted)' }}>Resolved Impact</div>
                            <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--lime)' }}>
                              {comparison.resolved_impacted_symbols.length}
                            </div>
                          </div>
                        </div>

                        {comparison.newly_impacted_symbols.length > 0 && (
                          <div style={{ marginBottom: '14px' }}>
                            <b style={{ fontSize: '13px', color: '#f59e0b' }}>Newly Affected Downstream Components:</b>
                            <ul style={{ margin: '6px 0', fontSize: '12px', fontFamily: 'var(--font-mono)' }}>
                              {comparison.newly_impacted_symbols.map((sym, i) => (
                                <li key={i}>{sym}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {comparison.newly_recommended_tests.length > 0 && (
                          <div>
                            <b style={{ fontSize: '13px', color: 'var(--lime)' }}>Newly Recommended Tests:</b>
                            <ul style={{ margin: '6px 0', fontSize: '12px', fontFamily: 'var(--font-mono)' }}>
                              {comparison.newly_recommended_tests.map((t, i) => (
                                <li key={i}>{t}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}
