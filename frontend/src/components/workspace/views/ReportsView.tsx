import { Activity, Download, FileText, GitCommitHorizontal, Info, Play, ShieldAlert } from 'lucide-react';
import { EmptyState } from '../../ui/EmptyState';
import { AnalysisRecord, ImpactAnalysisReport } from '../../../types';

interface ReportsViewProps {
  report: ImpactAnalysisReport | null;
  analyses?: AnalysisRecord[];
  onRunSample: () => void;
  isLoading: boolean;
}

export function ReportsView({ report, analyses = [], onRunSample, isLoading }: ReportsViewProps) {
  const hasReport = report !== null;
  const hasAnalyses = analyses.length > 0;
  const hasData = hasReport || hasAnalyses;

  const handleDownloadJSON = (rep?: ImpactAnalysisReport | null) => {
    const target = rep || report;
    if (!target) return;
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(target, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `changeradar-report-${target.head_commit.slice(0, 7)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="view-container">
      <section className="surface-card full-card">
        <div className="card-heading">
          <div>
            <h3>Audit & Impact Risk Reports</h3>
            <p>Reproducible, immutable change impact assessments stored in database</p>
          </div>
          {hasReport && (
            <button
              className="button button-lime button-small"
              onClick={() => handleDownloadJSON(report)}
              type="button"
            >
              <Download size={14} />
              <span>Export Audit JSON</span>
            </button>
          )}
        </div>

        <div style={{ margin: '8px 0 16px 0', padding: '10px 14px', borderRadius: '8px', background: 'rgba(199, 243, 107, 0.06)', border: '1px solid rgba(199, 243, 107, 0.15)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: 'var(--ws-text-muted)' }}>
          <Info size={16} color="var(--lime)" />
          <span><b>Methodology Note:</b> Risk scores represent <b>Heuristic structural risk (Not a probability of defect)</b> based on caller depth, symbol count, and contract changes.</span>
        </div>

        {hasData ? (
          <div className="reports-table">
            <div className="table-header">
              <span>HEAD COMMIT SHA</span>
              <span>BASE REVISION</span>
              <span>AFFECTED SYMBOLS</span>
              <span>RISK LEVEL</span>
              <span>EVALUATED AT</span>
            </div>

            {hasAnalyses ? (
              analyses.map((rec) => (
                <div key={rec.id} className="table-row-item">
                  <span className="mono-cell sha-cell">
                    <GitCommitHorizontal size={14} />
                    <b>{rec.head_commit.slice(0, 8)}</b>
                  </span>
                  <span className="mono-cell">{rec.base_commit.slice(0, 8)}</span>
                  <span className="count-cell">
                    <b>{rec.impacted_symbols_count}</b> symbols ({rec.changed_symbols_count} direct)
                  </span>
                  <span>
                    <span className={`risk-badge risk-${rec.risk_level}`}>
                      {rec.risk_level.toUpperCase()} ({rec.risk_score}/100)
                    </span>
                  </span>
                  <span className="date-cell">
                    {rec.created_at ? new Date(rec.created_at).toLocaleString() : 'Just now'}
                  </span>
                </div>
              ))
            ) : hasReport ? (
              <div className="table-row-item">
                <span className="mono-cell sha-cell">
                  <GitCommitHorizontal size={14} />
                  <b>{report.head_commit.slice(0, 8)}</b>
                </span>
                <span className="mono-cell">{report.base_commit.slice(0, 8)}</span>
                <span className="count-cell">
                  <b>{report.impacted_symbols.length}</b> symbols ({report.changed_symbols.length} direct)
                </span>
                <span>
                  <span className={`risk-badge risk-${report.risk_level}`}>
                    {report.risk_level.toUpperCase()} ({report.risk_score}/100)
                  </span>
                </span>
                <span className="date-cell">
                  {report.created_at ? new Date(report.created_at).toLocaleString() : 'Just now'}
                </span>
              </div>
            ) : null}

            {hasReport && (
              <div className="report-summary-box">
                <div className="summary-box-head">
                  <FileText size={18} />
                  <b>Latest Executive Analysis Summary</b>
                </div>
                <p>{report.summary_text}</p>
                <div className="summary-metrics-row">
                  <div>
                    <small>Repository Path</small>
                    <code>{report.repo_path}</code>
                  </div>
                  <div>
                    <small>AST Graph Size</small>
                    <span>{report.graph_nodes_count} symbols / {report.graph_edges_count} edges</span>
                  </div>
                  <div>
                    <small>Targeted Validation</small>
                    <span>{report.recommended_tests.length} test suites selected</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="reports-table-preview">
            <div className="table-header">
              <span>COMMIT SHA</span>
              <span>BASE REVISION</span>
              <span>AFFECTED SYMBOLS</span>
              <span>RISK LEVEL</span>
              <span>GENERATED AT</span>
            </div>

            <EmptyState
              title="Your historical reports will live here"
              description="Every completed analysis creates a permanent, evidence-backed audit report detailing downstream ripple effects."
              action="Run Sample Analysis"
              onAction={onRunSample}
              icon={<Activity size={28} />}
            />
          </div>
        )}
      </section>
    </div>
  );
}
