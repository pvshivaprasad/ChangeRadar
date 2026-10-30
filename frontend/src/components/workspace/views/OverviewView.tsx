import {
  Activity,
  ArrowRight,
  Check,
  CheckCircle2,
  GitBranch,
  Github,
  Play,
  Radar,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Workflow,
} from 'lucide-react';
import { EmptyState } from '../../ui/EmptyState';
import { ImpactAnalysisReport, PageId } from '../../../types';

interface OverviewViewProps {
  report: ImpactAnalysisReport | null;
  repositoriesCount?: number;
  analysesCount?: number;
  onConnectRepo: () => void;
  onNavigate: (page: PageId) => void;
  onRunSample: () => void;
  isAnalyzing: boolean;
}

export function OverviewView({
  report,
  repositoriesCount = 0,
  analysesCount = 0,
  onConnectRepo,
  onNavigate,
  onRunSample,
  isAnalyzing,
}: OverviewViewProps) {
  const hasData = report !== null;

  return (
    <div className="overview-container">
      {/* Welcome Panel */}
      <div className="welcome-panel">
        <div className="welcome-copy">
          <div className="welcome-kicker">
            <Sparkles size={15} />
            <span>
              {hasData ? 'LIVE ANALYSIS COMPLETE' : 'WORKSPACE INITIALIZED & READY'}
            </span>
          </div>
          <h2>
            {hasData ? (
              <>
                Impact analysis
                <br />
                <em>active.</em>
              </>
            ) : (
              <>
                Connect your first
                <br />
                <em>codebase.</em>
              </>
            )}
          </h2>
          <p>
            {hasData
              ? report.summary_text
              : 'ChangeRadar statically parses Python AST to construct an immutable symbol dependency graph. Trace call hierarchies and discover potential change impact across modules before merging.'}
          </p>
          <div className="welcome-actions">
            <button
              className="button button-lime button-panel"
              onClick={onRunSample}
              disabled={isAnalyzing}
              type="button"
            >
              <Play size={16} />
              <span>
                {isAnalyzing ? 'Running AST Analysis...' : 'Run Verified Sample Analysis'}
              </span>
            </button>
            <button
              className="button button-ghost button-panel"
              onClick={() => onNavigate('analysis')}
              type="button"
            >
              <span>View full change impact</span>
            </button>
          </div>
        </div>

        <div className="welcome-visual" aria-hidden="true">
          <div className="welcome-orbit orbit-a" />
          <div className="welcome-orbit orbit-b" />
          <div className="welcome-core">
            <Radar size={42} strokeWidth={2} />
          </div>
          <div className="floating-chip chip-a">
            <GitBranch size={15} />
            <span>{hasData ? `${report.changed_symbols.length} modified symbols` : 'AST symbol extraction'}</span>
          </div>
          <div className="floating-chip chip-b">
            <Workflow size={15} />
            <span>{hasData ? `${report.graph_edges_count} dependency edges` : 'Dependency DAG'}</span>
          </div>
          <div className="floating-chip chip-c">
            <ShieldCheck size={15} />
            <span>{hasData ? `${report.risk_level.toUpperCase()} RISK` : 'Impact reports'}</span>
          </div>
        </div>
      </div>

      {/* Metric Cards: Displays real repository metrics if analyzed */}
      <div className="metric-grid">
        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Repositories Scanned</span>
            <Github size={18} className="metric-icon" />
          </div>
          <strong className="metric-value">
            {repositoriesCount > 0 ? repositoriesCount : (hasData ? '1' : '0')}
          </strong>
          <span className="metric-subtext">
            {repositoriesCount > 0
              ? `${repositoriesCount} active local ${repositoriesCount === 1 ? 'repository' : 'repositories'} connected`
              : (hasData ? 'synthetic_repo (verified fixture)' : 'Waiting for first repository')}
          </span>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Impact Analyses Run</span>
            <Activity size={18} className="metric-icon" />
          </div>
          <strong className="metric-value">
            {analysesCount > 0 ? analysesCount : (hasData ? '1' : '0')}
          </strong>
          <span className="metric-subtext">
            {hasData
              ? `Commit ${report.head_commit.slice(0, 7)} vs ${report.base_commit.slice(0, 7)}`
              : (analysesCount > 0 ? `${analysesCount} change reports generated` : 'Awaiting pull request scan')}
          </span>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Impacted Downstream Symbols</span>
            <Workflow size={18} className="metric-icon" />
          </div>
          <strong className="metric-value">{hasData ? report.impacted_symbols.length : '—'}</strong>
          <span className="metric-subtext">
            {hasData ? `${report.graph_nodes_count} symbols mapped in AST graph` : 'Computed from AST call graph'}
          </span>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Targeted Tests Suggested</span>
            <Check size={18} className="metric-icon" />
          </div>
          <strong className="metric-value">{hasData ? report.recommended_tests.length : '—'}</strong>
          <span className="metric-subtext">
            {hasData ? 'Mapped directly to modified code paths' : 'Deterministic path coverage'}
          </span>
        </div>
      </div>

      {/* Lower Dashboard Grid */}
      <div className="lower-grid">
        {/* Recent Activity Card */}
        <section className="surface-card recent-card">
          <div className="card-heading">
            <div>
              <h3>Recent Repository Activity</h3>
              <p>Chronological feed of scans, commits, and impact evaluations</p>
            </div>
            <button
              className="quiet-button"
              onClick={() => onNavigate('reports')}
              type="button"
            >
              <span>View all reports</span>
              <ArrowRight size={15} />
            </button>
          </div>

          {hasData ? (
            <div className="real-activity-list">
              <div
                className="activity-item"
                onClick={() => onNavigate('analysis')}
                style={{ cursor: 'pointer' }}
                title="Click to inspect this change impact evaluation"
              >
                <div className="activity-icon-badge">
                  <CheckCircle2 size={18} color="#8bb736" />
                </div>
                <div className="activity-details">
                  <b>Evaluated commit {report.head_commit.slice(0, 7)} against {report.base_commit.slice(0, 7)}</b>
                  <p>{report.summary_text}</p>
                  <small>{new Date(report.created_at).toLocaleTimeString()} · Click to inspect full report</small>
                </div>
                <span className={`risk-badge risk-${report.risk_level}`}>
                  {report.risk_level.toUpperCase()}
                </span>
              </div>
            </div>
          ) : (
            <EmptyState
              title="No activity recorded yet"
              description="Your repository scan events and PR impact evaluations will appear here. Click 'Run Verified Sample Analysis' above to test the live pipeline."
              action="Run Sample Analysis"
              onAction={onRunSample}
            />
          )}
        </section>

        {/* Getting Started Checklist */}
        <section className="surface-card getting-card">
          <div className="card-heading">
            <div>
              <h3>Getting Started with ChangeRadar</h3>
              <p>Key setup milestones for your engineering workspace</p>
            </div>
            <span className="progress-label">{hasData ? '3 of 3 completed' : '0 of 3 completed'}</span>
          </div>

          <div className="checklist">
            <div
              className="checklist-item"
              onClick={onConnectRepo}
              role="button"
              tabIndex={0}
            >
              <span className={`step-number ${hasData ? 'step-completed' : ''}`}>
                {hasData ? '✓' : '01'}
              </span>
              <div className="step-content">
                <b>Connect a GitHub repository</b>
                <small>{hasData ? 'Connected synthetic_repo fixture' : 'Link a Python codebase for static scanning'}</small>
              </div>
              <ArrowRight size={16} className="step-arrow" />
            </div>

            <div
              className="checklist-item"
              onClick={() => onNavigate('dependencies')}
              role="button"
              tabIndex={0}
            >
              <span className={`step-number ${hasData ? 'step-completed' : ''}`}>
                {hasData ? '✓' : '02'}
              </span>
              <div className="step-content">
                <b>Build your code map</b>
                <small>{hasData ? `${report.graph_nodes_count} symbols & ${report.graph_edges_count} edges mapped` : 'Extract functions, classes, and cross-module dependency edges'}</small>
              </div>
              <ArrowRight size={16} className="step-arrow" />
            </div>

            <div
              className="checklist-item"
              onClick={() => onNavigate('analysis')}
              role="button"
              tabIndex={0}
            >
              <span className={`step-number ${hasData ? 'step-completed' : ''}`}>
                {hasData ? '✓' : '03'}
              </span>
              <div className="step-content">
                <b>Run a change impact analysis</b>
                <small>{hasData ? `${report.impacted_symbols.length} impacted symbols surfaced` : 'Compare two commit SHAs and discover downstream ripple risks'}</small>
              </div>
              <ArrowRight size={16} className="step-arrow" />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
