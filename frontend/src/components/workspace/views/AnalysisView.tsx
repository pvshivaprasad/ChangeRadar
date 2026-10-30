import { useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  Boxes,
  Braces,
  CheckCircle2,
  FileCode,
  GitBranch,
  GitCommitHorizontal,
  Info,
  Play,
  RotateCcw,
  ShieldAlert,
  Sparkles,
  Workflow,
  Zap,
} from 'lucide-react';
import { EmptyState } from '../../ui/EmptyState';
import { ImpactAnalysisReport } from '../../../types';

interface AnalysisViewProps {
  report: ImpactAnalysisReport | null;
  onNavigate: () => void;
  onRunSample: () => void;
  onCustomAnalyze: (repoPath: string, base: string, head: string) => void;
  isAnalyzing: boolean;
  error: string | null;
}

export function AnalysisView({
  report,
  onNavigate,
  onRunSample,
  onCustomAnalyze,
  isAnalyzing,
  error,
}: AnalysisViewProps) {
  const [repoPath, setRepoPath] = useState('');
  const [baseBranch, setBaseBranch] = useState('HEAD~1');
  const [headBranch, setHeadBranch] = useState('HEAD');

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoPath.trim()) {
      onRunSample();
    } else {
      onCustomAnalyze(repoPath.trim(), baseBranch.trim(), headBranch.trim());
    }
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
          <div className="compare-header-actions">
            <button
              className="button button-lime button-small"
              onClick={onRunSample}
              disabled={isAnalyzing}
              type="button"
            >
              <Play size={14} />
              <span>{isAnalyzing ? 'Analyzing...' : 'Run Sample Fixture'}</span>
            </button>
            <span className="status-pill">
              <i /> ENGINE READY
            </span>
          </div>
        </div>

        <form onSubmit={handleCustomSubmit} className="compare-inputs">
          <div className="branch-selector">
            <label htmlFor="custom-repo-path">Local Repository Path (or leave blank for fixture)</label>
            <div className="input-with-icon">
              <FileCode size={16} />
              <input
                id="custom-repo-path"
                type="text"
                value={repoPath}
                onChange={(e) => setRepoPath(e.target.value)}
                placeholder="D:\Movies\ChangeRadar-v0.1.1\changeradar\backend\tests\fixtures\synthetic_repo"
              />
            </div>
          </div>

          <div className="branch-selector">
            <label htmlFor="base-branch">Base Revision</label>
            <div className="input-with-icon">
              <GitBranch size={16} />
              <input
                id="base-branch"
                type="text"
                value={baseBranch}
                onChange={(e) => setBaseBranch(e.target.value)}
                placeholder="HEAD~1 or commit SHA"
              />
            </div>
          </div>

          <div className="compare-arrow">
            <ArrowRight size={20} />
          </div>

          <div className="branch-selector">
            <label htmlFor="head-branch">Head Revision</label>
            <div className="input-with-icon">
              <GitCommitHorizontal size={16} />
              <input
                id="head-branch"
                type="text"
                value={headBranch}
                onChange={(e) => setHeadBranch(e.target.value)}
                placeholder="HEAD or commit SHA"
              />
            </div>
          </div>

          <button
            className="button button-lime run-analysis-btn"
            type="submit"
            disabled={isAnalyzing}
          >
            <Play size={16} />
            <span>{isAnalyzing ? 'Analyzing...' : 'Analyze Impact'}</span>
          </button>
        </form>

        {error && (
          <div className="inline-notice compare-notice notice-error">
            <AlertTriangle size={15} />
            <span>{error}</span>
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

      {/* Real Analysis Output if Available */}
      {report ? (
        <div className="analysis-results-grid">
          {/* Executive Risk Banner */}
          <div className="surface-card risk-banner-card">
            <div className="risk-banner-header">
              <div className="risk-banner-title">
                <ShieldAlert size={22} color={report.risk_level === 'high' ? '#d66e68' : '#d9a15f'} />
                <div>
                  <h4>Risk Evaluation: {report.risk_level.toUpperCase()} (Score: {report.risk_score} / 100)</h4>
                  <p>{report.summary_text}</p>
                </div>
              </div>
              <div className="risk-meta-stats">
                <div className="meta-stat">
                  <b>{report.changed_symbols.length}</b>
                  <span>Changed symbols</span>
                </div>
                <div className="meta-stat">
                  <b>{report.impacted_symbols.length}</b>
                  <span>Impacted callers</span>
                </div>
                <div className="meta-stat">
                  <b>{report.recommended_tests.length}</b>
                  <span>Targeted tests</span>
                </div>
              </div>
            </div>
          </div>

          {/* Changed Symbols Section */}
          <section className="surface-card">
            <div className="card-heading">
              <div>
                <h3>1. Directly Modified Symbols (from Git Diff)</h3>
                <p>Functions, methods, and classes with added or modified lines in this revision</p>
              </div>
              <span className="subtle-count">{report.changed_symbols.length} symbols modified</span>
            </div>

            <div className="symbol-table">
              <div className="symbol-table-header">
                <span>SYMBOL NAME</span>
                <span>TYPE</span>
                <span>FILE LOCATION</span>
                <span>LINE RANGE</span>
              </div>
              {report.changed_symbols.map((sym) => (
                <div key={sym.id} className="symbol-table-row modified-row">
                  <span className="symbol-name-col">
                    <Braces size={15} color="#8bb736" />
                    <b>{sym.name}</b>
                    <small>{sym.id}</small>
                  </span>
                  <span className="symbol-badge">{sym.symbol_type.toUpperCase()}</span>
                  <span className="symbol-file-col">{sym.file_path}</span>
                  <span className="symbol-lines-col">L{sym.line_start} - L{sym.line_end}</span>
                </div>
              ))}
            </div>
          </section>

          {/* Blast Radius Traversal Section */}
          <section className="surface-card">
            <div className="card-heading">
              <div>
                <h3>2. Downstream Blast Radius (AST Call Graph Traversal)</h3>
                <p>All callers, importers, and consumers identified by reverse graph traversal</p>
              </div>
              <span className="subtle-count">{report.impacted_symbols.length} affected symbols</span>
            </div>

            <div className="impact-tree-list">
              {report.impacted_symbols.map((imp) => {
                const isDirectChange = imp.depth === 0;
                return (
                  <div
                    key={`${imp.symbol_id}-${imp.depth}`}
                    className={`impact-node-card depth-${imp.depth}`}
                  >
                    <div className="impact-node-header">
                      <span className={`depth-pill depth-pill-${imp.depth}`}>
                        {isDirectChange ? 'DIRECT CHANGE' : `DEPTH ${imp.depth}: ${imp.impact_type.toUpperCase()}`}
                      </span>
                      <span className="impact-file-tag">{imp.file_path}:L{imp.line_start}</span>
                    </div>
                    <div className="impact-node-body">
                      <b>{imp.symbol_name}</b>
                      <small className="impact-id-text">{imp.symbol_id}</small>
                    </div>
                    {imp.path_from_change.length > 1 && (
                      <div className="impact-path-breadcrumb">
                        <span>Path from root:</span>
                        {imp.path_from_change.map((p, idx) => (
                          <span key={idx} className="path-step">
                            {idx > 0 && <span className="path-arrow">&rarr;</span>}
                            <code>{p.split('.').slice(-2).join('.')}</code>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        </div>
      ) : (
        <section className="surface-card full-card">
          <div className="card-heading">
            <div>
              <h3>Impact Findings & Call Graph Traversal</h3>
              <p>Directly modified functions, downstream callers, and contract boundaries</p>
            </div>
            <span className="subtle-count">0 symbols analyzed</span>
          </div>

          <EmptyState
            title="Ready to run change impact analysis"
            description="Click 'Run Sample Fixture' above to immediately analyze a verified pull request modifying auth token validation and inspect its blast radius."
            action="Run Sample Analysis"
            onAction={onRunSample}
            icon={<GitBranch size={28} />}
          />
        </section>
      )}
    </div>
  );
}
