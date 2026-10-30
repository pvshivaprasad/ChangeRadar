import React from 'react';
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  FileCode,
  GitBranch,
  GitCommitHorizontal,
  Layers,
  Shield,
  ShieldAlert,
  TestTube2,
  Workflow,
} from 'lucide-react';
import { ImpactAnalysisReport } from '../../../types';

interface AnalysisOverviewCardProps {
  report: ImpactAnalysisReport;
  repoName?: string;
}

export const AnalysisOverviewCard: React.FC<AnalysisOverviewCardProps> = ({
  report,
  repoName,
}) => {
  const shortBase = report.base_commit.slice(0, 7);
  const shortHead = report.head_commit.slice(0, 7);
  const displayName = repoName || report.repo_path.split(/[\\/]/).pop() || 'Repository';

  // Compute plain English narrative based on real analysis data
  const directCount = report.changed_symbols.length;
  const directDependents = report.impacted_symbols.filter((s) => s.depth === 1).length;
  const indirectDependents = report.impacted_symbols.filter((s) => s.depth >= 2).length;
  const testCount = report.recommended_tests.length;

  let narrativeText = '';
  const article = report.risk_level === 'elevated' ? 'an' : 'a';
  if (directCount === 0) {
    narrativeText = `No Python function or class modifications were detected between revisions ${shortBase} and ${shortHead}. Documentation or non-code files may have changed.`;
  } else if (report.risk_level === 'high' || report.risk_level === 'elevated') {
    narrativeText = `Modifications in ${directCount} symbol${directCount > 1 ? 's' : ''} across ${report.changed_files.length} file${report.changed_files.length > 1 ? 's' : ''} trigger ${article} ${report.risk_level} ripple effect: ${directDependents} direct caller${directDependents !== 1 ? 's' : ''} and ${indirectDependents} indirect component${indirectDependents !== 1 ? 's' : ''} rely on this code path. Running ${testCount} targeted test${testCount !== 1 ? 's' : ''} is recommended before merging.`;
  } else {
    narrativeText = `Modifications in ${directCount} symbol${directCount > 1 ? 's' : ''} across ${report.changed_files.length} file${report.changed_files.length > 1 ? 's' : ''} have a localized impact. Only ${directDependents} direct caller${directDependents !== 1 ? 's' : ''} depend on altered code. ${testCount} targeted test${testCount !== 1 ? 's' : ''} will verify these changes.`;
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high':
        return '#d66e68';
      case 'elevated':
        return '#d9a15f';
      case 'medium':
        return '#e0b468';
      default:
        return 'var(--lime)';
    }
  };

  const riskColor = getRiskColor(report.risk_level);

  return (
    <div className="surface-card visual-overview-card">
      <div className="visual-overview-header">
        <div className="overview-title-group">
          <div className="overview-kicker">
            <span className="status-dot-pulse" />
            <span>ANALYSIS COMPLETE</span>
            <span className="overview-sep">&bull;</span>
            <Clock size={13} />
            <span>{new Date(report.created_at).toLocaleString()}</span>
          </div>
          <h2>
            Changes in <span className="highlight-repo">{displayName}</span>
          </h2>
          <div className="revisions-badge-strip">
            <span className="rev-badge base-badge">
              <GitBranch size={13} />
              <code>{shortBase}</code>
            </span>
            <ArrowRight size={14} className="rev-arrow" />
            <span className="rev-badge head-badge">
              <GitCommitHorizontal size={13} />
              <code>{shortHead}</code>
            </span>
            <span className="engine-verified-tag">
              <CheckCircle2 size={13} color="var(--lime)" />
              <span>AST Graph Verified</span>
            </span>
          </div>
        </div>

        {/* Risk Score Pill */}
        <div className="overview-risk-gauge" style={{ borderColor: riskColor }}>
          <div className="risk-gauge-score" style={{ color: riskColor }}>
            <span className="score-num">{Math.round(report.risk_score)}</span>
            <span className="score-max">/100</span>
          </div>
          <div className="risk-gauge-label">
            <span className="risk-level-tag" style={{ background: `${riskColor}22`, color: riskColor }}>
              {report.risk_level.toUpperCase()} RISK
            </span>
            <small>Blast Radius Index</small>
          </div>
        </div>
      </div>

      {/* Plain-English Narrative */}
      <div className="plain-narrative-box">
        <p>{narrativeText}</p>
      </div>

      {/* At-a-Glance Metric Strip */}
      <div className="visual-metrics-grid">
        <div className="visual-metric-box">
          <div className="metric-icon-wrap">
            <FileCode size={20} color="var(--ws-text-muted)" />
          </div>
          <div className="metric-info">
            <strong className="metric-number">{report.changed_files.length}</strong>
            <span className="metric-label">Files Changed</span>
          </div>
        </div>

        <div className="visual-metric-box">
          <div className="metric-icon-wrap">
            <Layers size={20} color="var(--lime)" />
          </div>
          <div className="metric-info">
            <strong className="metric-number">{report.changed_symbols.length}</strong>
            <span className="metric-label">Symbols Modified</span>
          </div>
        </div>

        <div className="visual-metric-box">
          <div className="metric-icon-wrap">
            <Workflow size={20} color="var(--amber)" />
          </div>
          <div className="metric-info">
            <strong className="metric-number">{report.impacted_symbols.length}</strong>
            <span className="metric-label">Components Affected</span>
          </div>
        </div>

        <div className="visual-metric-box">
          <div className="metric-icon-wrap">
            <TestTube2 size={20} color="var(--violet)" />
          </div>
          <div className="metric-info">
            <strong className="metric-number">{report.recommended_tests.length}</strong>
            <span className="metric-label">Recommended Tests</span>
          </div>
        </div>
      </div>
    </div>
  );
};
