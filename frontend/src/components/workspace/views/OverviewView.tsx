import {
  Activity,
  ArrowRight,
  Check,
  GitBranch,
  Github,
  Radar,
  ShieldCheck,
  Sparkles,
  Workflow,
} from 'lucide-react';
import { EmptyState } from '../../ui/EmptyState';
import { PageId } from '../../../types';

interface OverviewViewProps {
  onConnectRepo: () => void;
  onNavigate: (page: PageId) => void;
}

export function OverviewView({ onConnectRepo, onNavigate }: OverviewViewProps) {
  return (
    <div className="overview-container">
      {/* Welcome Panel */}
      <div className="welcome-panel">
        <div className="welcome-copy">
          <div className="welcome-kicker">
            <Sparkles size={15} />
            <span>WORKSPACE INITIALIZED & READY</span>
          </div>
          <h2>
            Connect your first
            <br />
            <em>codebase.</em>
          </h2>
          <p>
            ChangeRadar statically parses Python AST to construct an immutable
            symbol dependency graph. Trace call hierarchies and discover potential
            change impact across modules before merging.
          </p>
          <div className="welcome-actions">
            <button
              className="button button-lime button-panel"
              onClick={onConnectRepo}
              type="button"
            >
              <span>Connect GitHub repository</span>
              <ArrowRight size={17} />
            </button>
            <button
              className="button button-ghost button-panel"
              onClick={() => onNavigate('analysis')}
              type="button"
            >
              <span>Inspect analysis pipeline</span>
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
            <span>AST symbol extraction</span>
          </div>
          <div className="floating-chip chip-b">
            <Workflow size={15} />
            <span>Dependency DAG</span>
          </div>
          <div className="floating-chip chip-c">
            <ShieldCheck size={15} />
            <span>Impact reports</span>
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="metric-grid">
        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Repositories Connected</span>
            <Github size={18} className="metric-icon" />
          </div>
          <strong className="metric-value">—</strong>
          <span className="metric-subtext">Waiting for first repository</span>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Impact Analyses Run</span>
            <Activity size={18} className="metric-icon" />
          </div>
          <strong className="metric-value">—</strong>
          <span className="metric-subtext">Awaiting pull request scan</span>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Dependencies Mapped</span>
            <Workflow size={18} className="metric-icon" />
          </div>
          <strong className="metric-value">—</strong>
          <span className="metric-subtext">Computed from AST call graph</span>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Targeted Tests Suggested</span>
            <Check size={18} className="metric-icon" />
          </div>
          <strong className="metric-value">—</strong>
          <span className="metric-subtext">Deterministic path coverage</span>
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
          <EmptyState
            title="No activity recorded yet"
            description="Your repository scan events and PR impact evaluations will appear here once you link a codebase."
            action="Connect a repository"
            onAction={onConnectRepo}
          />
        </section>

        {/* Getting Started Checklist */}
        <section className="surface-card getting-card">
          <div className="card-heading">
            <div>
              <h3>Getting Started with ChangeRadar</h3>
              <p>Key setup milestones for your engineering workspace</p>
            </div>
            <span className="progress-label">0 of 3 completed</span>
          </div>

          <div className="checklist">
            <div
              className="checklist-item"
              onClick={onConnectRepo}
              role="button"
              tabIndex={0}
            >
              <span className="step-number">01</span>
              <div className="step-content">
                <b>Connect a GitHub repository</b>
                <small>Link a public or private Python codebase for static scanning</small>
              </div>
              <ArrowRight size={16} className="step-arrow" />
            </div>

            <div
              className="checklist-item"
              onClick={() => onNavigate('dependencies')}
              role="button"
              tabIndex={0}
            >
              <span className="step-number">02</span>
              <div className="step-content">
                <b>Build your first code map</b>
                <small>Extract functions, classes, and cross-module dependency edges</small>
              </div>
              <ArrowRight size={16} className="step-arrow" />
            </div>

            <div
              className="checklist-item"
              onClick={() => onNavigate('analysis')}
              role="button"
              tabIndex={0}
            >
              <span className="step-number">03</span>
              <div className="step-content">
                <b>Run a change impact analysis</b>
                <small>Compare two commit SHAs and discover downstream ripple risks</small>
              </div>
              <ArrowRight size={16} className="step-arrow" />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
