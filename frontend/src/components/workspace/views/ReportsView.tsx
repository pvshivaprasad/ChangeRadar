import { Activity, Calendar, Download, FileText, GitCommitHorizontal, Play, ShieldAlert } from 'lucide-react';
import { EmptyState } from '../../ui/EmptyState';
import { ImpactAnalysisReport } from '../../../types';

interface ReportsViewProps {
  report: ImpactAnalysisReport | null;
  onRunSample: () => void;
  isLoading: boolean;
}

export function ReportsView({ report, onRunSample, isLoading }: ReportsViewProps) {
  const hasData = report !== null;

  const handleDownloadJSON = () => {
    if (!report) return;
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(report, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `changeradar-report-${report.head_commit.slice(0, 7)}.json`);
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
            <p>Reproducible change assessments linked to immutable Git commit SHAs</p>
          </div>
          {hasData && (
            <button
              className="button button-lime button-small"
              onClick={handleDownloadJSON}
              type="button"
            >
              <Download size={14} />
              <span>Export Audit JSON</span>
            </button>
          )}
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
                  {report.risk_level.toUpperCase()} ({report.risk_score})
                </span>
              </span>
              <span className="date-cell">
                {new Date(report.created_at).toLocaleString()}
              </span>
            </div>

            <div className="report-summary-box">
              <div className="summary-box-head">
                <FileText size={18} />
                <b>Executive Analysis Summary</b>
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
