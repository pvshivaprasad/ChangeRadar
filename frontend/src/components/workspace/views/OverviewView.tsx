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
    <>
      <div className="welcome-panel">
        <div className="welcome-copy">
          <span className="welcome-kicker">
            <Sparkles size={14} /> YOUR WORKSPACE IS READY
          </span>
          <h2>
            Start with a<br />
            <em>repository.</em>
          </h2>
          <p>
            Connect a GitHub codebase to map dependencies, surface potential
            change risk, and discover relevant tests before merging.
          </p>
          <button
            className="button button-lime"
            onClick={onConnectRepo}
            type="button"
          >
            Connect a repository <ArrowRight size={16} />
          </button>
        </div>

        <div className="welcome-visual" aria-hidden="true">
          <div className="welcome-orbit orbit-a" />
          <div className="welcome-orbit orbit-b" />
          <div className="welcome-core">
            <Radar size={37} />
          </div>
          <div className="floating-chip chip-a">
            <GitBranch size={14} /> Source code
          </div>
          <div className="floating-chip chip-b">
            <Workflow size={14} /> Dependencies
          </div>
          <div className="floating-chip chip-c">
            <ShieldCheck size={14} /> Impact insights
          </div>
        </div>
      </div>

      <div className="metric-grid">
        <div className="metric-card">
          <div className="metric-top">
            <span>Repositories</span>
            <Github size={16} />
          </div>
          <strong>—</strong>
          <small>Connect your first repository</small>
        </div>
        <div className="metric-card">
          <div className="metric-top">
            <span>Analyses run</span>
            <Activity size={16} />
          </div>
          <strong>—</strong>
          <small>Waiting for your first analysis</small>
        </div>
        <div className="metric-card">
          <div className="metric-top">
            <span>Potential impacts</span>
            <Workflow size={16} />
          </div>
          <strong>—</strong>
          <small>Computed from dependency graph</small>
        </div>
        <div className="metric-card">
          <div className="metric-top">
            <span>Tests suggested</span>
            <Check size={16} />
          </div>
          <strong>—</strong>
          <small>Insights from changed symbols</small>
        </div>
      </div>

      <div className="lower-grid">
        <section className="surface-card recent-card">
          <div className="card-heading">
            <div>
              <h3>Recent activity</h3>
              <p>Your latest repository and analysis events</p>
            </div>
            <button
              className="quiet-button"
              onClick={() => onNavigate('reports')}
              type="button"
            >
              View all <ArrowRight size={14} />
            </button>
          </div>
          <EmptyState
            title="Nothing here just yet"
            description="Your repository activity and analysis history will show up here once you get connected."
          />
        </section>

        <section className="surface-card getting-card">
          <div className="card-heading">
            <div>
              <h3>Getting started</h3>
              <p>Your first steps with ChangeRadar</p>
            </div>
            <span className="progress-label">0 of 3</span>
          </div>
          <div className="checklist">
            <div
              className="checklist-item"
              onClick={onConnectRepo}
              role="button"
              tabIndex={0}
            >
              <span className="step-number">01</span>
              <span>
                <b>Connect a repository</b>
                <small>Bring in a GitHub codebase</small>
              </span>
              <ArrowRight size={15} />
            </div>
            <div
              className="checklist-item"
              onClick={() => onNavigate('dependencies')}
              role="button"
              tabIndex={0}
            >
              <span className="step-number">02</span>
              <span>
                <b>Build your code map</b>
                <small>Discover modules and dependencies</small>
              </span>
              <ArrowRight size={15} />
            </div>
            <div
              className="checklist-item"
              onClick={() => onNavigate('analysis')}
              role="button"
              tabIndex={0}
            >
              <span className="step-number">03</span>
              <span>
                <b>Run an impact analysis</b>
                <small>Review your first change</small>
              </span>
              <ArrowRight size={15} />
            </div>
          </div>
        </section>
      </div>
    </>
  );
}
