import { useState } from 'react';
import { ArrowRight, GitBranch, GitCommitHorizontal, Info, Play, ShieldAlert, Sparkles } from 'lucide-react';
import { EmptyState } from '../../ui/EmptyState';

export function AnalysisView({ onNavigate }: { onNavigate: () => void }) {
  const [baseBranch, setBaseBranch] = useState('main');
  const [headBranch, setHeadBranch] = useState('feature/auth-rework');
  const [notice, setNotice] = useState<string | null>(null);

  const handleRunAnalysis = () => {
    setNotice(
      'Git diff processor and AST symbol traversal engine will run live scans in Milestone 2. Connect a repository first.'
    );
  };

  return (
    <div className="view-container">
      {/* Revision Comparison Bar */}
      <div className="surface-card compare-card">
        <div className="compare-header">
          <div>
            <h3>Change Impact Comparator</h3>
            <p>Select base and head Git revisions to evaluate potential downstream blast radius</p>
          </div>
          <span className="status-pill">
            <i /> ANALYSIS ENGINE READY
          </span>
        </div>

        <div className="compare-inputs">
          <div className="branch-selector">
            <label htmlFor="base-branch">Base Revision (Target)</label>
            <div className="input-with-icon">
              <GitBranch size={16} />
              <input
                id="base-branch"
                type="text"
                value={baseBranch}
                onChange={(e) => setBaseBranch(e.target.value)}
                placeholder="main or commit SHA"
              />
            </div>
          </div>

          <div className="compare-arrow">
            <ArrowRight size={20} />
          </div>

          <div className="branch-selector">
            <label htmlFor="head-branch">Head Revision (Proposed Change)</label>
            <div className="input-with-icon">
              <GitCommitHorizontal size={16} />
              <input
                id="head-branch"
                type="text"
                value={headBranch}
                onChange={(e) => setHeadBranch(e.target.value)}
                placeholder="branch name or PR commit SHA"
              />
            </div>
          </div>

          <button
            className="button button-lime run-analysis-btn"
            onClick={handleRunAnalysis}
            type="button"
          >
            <Play size={16} />
            <span>Analyze Impact</span>
          </button>
        </div>

        {notice && (
          <div className="inline-notice compare-notice">
            <Info size={15} />
            <span>{notice}</span>
          </div>
        )}
      </div>

      {/* Analysis Pipeline Guidance */}
      <div className="pipeline-strip">
        <div className="pipeline-step">
          <span className="step-tag">01</span>
          <span>Git Diff Ingestion</span>
        </div>
        <div className="pipeline-arrow">&rarr;</div>
        <div className="pipeline-step">
          <span className="step-tag">02</span>
          <span>AST Symbol Extraction</span>
        </div>
        <div className="pipeline-arrow">&rarr;</div>
        <div className="pipeline-step">
          <span className="step-tag">03</span>
          <span>Dependency Graph Traversal</span>
        </div>
        <div className="pipeline-arrow">&rarr;</div>
        <div className="pipeline-step">
          <span className="step-tag">04</span>
          <span>Targeted Test Mapping</span>
        </div>
      </div>

      {/* Primary Card */}
      <section className="surface-card full-card">
        <div className="card-heading">
          <div>
            <h3>Impact Findings & Call Graph Traversal</h3>
            <p>Directly modified functions, downstream callers, and contract boundaries</p>
          </div>
          <span className="subtle-count">0 symbols analyzed</span>
        </div>

        <EmptyState
          title="No repository selected for comparison"
          description="Connect a repository first. Once connected, ChangeRadar will compare revisions against immutable commit SHAs."
          action="Go to repositories"
          onAction={onNavigate}
          icon={<GitBranch size={26} />}
        />
      </section>
    </div>
  );
}
