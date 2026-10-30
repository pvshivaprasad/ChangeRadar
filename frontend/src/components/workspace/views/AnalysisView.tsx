import React, { useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  Boxes,
  Braces,
  Check,
  CheckCircle2,
  Code2,
  Copy,
  Cpu,
  FileCode,
  GitBranch,
  GitCommitHorizontal,
  History,
  Info,
  Layers,
  Network,
  Play,
  RotateCcw,
  Shield,
  ShieldAlert,
  Sparkles,
  Terminal,
  Workflow,
  Zap,
} from 'lucide-react';
import { EmptyState } from '../../ui/EmptyState';
import { AnalysisRecord, ImpactAnalysisReport } from '../../../types';
import { AnalysisOverviewCard } from '../analysis/AnalysisOverviewCard';
import { WhatChangedSection } from '../analysis/WhatChangedSection';
import { InteractiveImpactMap } from '../analysis/InteractiveImpactMap';
import { WhatToTestSection } from '../analysis/WhatToTestSection';
import { RiskExplanationCard } from '../analysis/RiskExplanationCard';
import { GuidedSampleTour } from '../analysis/GuidedSampleTour';

interface AnalysisViewProps {
  report: ImpactAnalysisReport | null;
  analyses?: AnalysisRecord[];
  onSelectAnalysis?: (analysis: AnalysisRecord) => void;
  onNavigate: () => void;
  onRunSample: () => void;
  onCustomAnalyze: (repoPath: string, base: string, head: string) => void;
  isAnalyzing: boolean;
  error: string | null;
}

export function AnalysisView({
  report,
  analyses = [],
  onSelectAnalysis,
  onNavigate,
  onRunSample,
  onCustomAnalyze,
  isAnalyzing,
  error,
}: AnalysisViewProps) {
  const [repoPath, setRepoPath] = useState('');
  const [baseBranch, setBaseBranch] = useState('HEAD~1');
  const [headBranch, setHeadBranch] = useState('HEAD');
  const [viewMode, setViewMode] = useState<'simple' | 'technical'>('simple');
  const [copiedRawDiff, setCopiedRawDiff] = useState(false);

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoPath.trim()) {
      onRunSample();
    } else {
      onCustomAnalyze(repoPath.trim(), baseBranch.trim(), headBranch.trim());
    }
  };

  const handleCopyRawDiff = () => {
    if (!report || !report.file_diffs) return;
    const fullDiff = report.file_diffs.map((f) => f.diff_content || '').join('\n');
    navigator.clipboard.writeText(fullDiff);
    setCopiedRawDiff(true);
    setTimeout(() => setCopiedRawDiff(false), 2000);
  };

  // Find active analysis record to display friendly repo name
  const activeRecord = analyses.find(
    (a) =>
      report &&
      (a.head_commit === report.head_commit ||
        (a.report && a.report.created_at === report.created_at))
  );

  return (
    <div className="view-container analysis-view-v2">
      {/* 1. Revision Comparison Bar */}
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

        {/* Saved Analyses Quick-Switcher */}
        {analyses && analyses.length > 0 && (
          <div className="saved-analyses-bar">
            <span className="saved-analyses-label">
              <History size={14} color="var(--lime)" /> Saved Analyses ({analyses.length}):
            </span>
            <div className="saved-analyses-chips">
              {analyses.slice(0, 6).map((rec) => {
                const isActive =
                  report &&
                  (report.head_commit === rec.head_commit ||
                    (rec.report && rec.report.created_at === report.created_at));
                const isCompleted = rec.status === 'completed';
                return (
                  <button
                    key={rec.id}
                    type="button"
                    onClick={() => onSelectAnalysis && rec.report && onSelectAnalysis(rec)}
                    disabled={!isCompleted || !rec.report}
                    title={rec.summary_text || undefined}
                    className={`history-chip ${isActive ? 'active' : ''}`}
                  >
                    <span>{rec.repo_name || 'Repository'}</span>
                    <code>{rec.head_commit.slice(0, 7)}</code>
                    <span className={`chip-risk-pill risk-${rec.risk_level}`}>
                      {rec.risk_level}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* 2. First-Time Usability: Guided Sample Tour */}
      <GuidedSampleTour
        onRunSample={onRunSample}
        isAnalyzing={isAnalyzing}
        hasReport={report !== null}
      />

      {/* 3. Analysis Findings & Results */}
      {report ? (
        <div className="analysis-content-wrapper">
          {/* View Mode Switcher Header */}
          <div className="analysis-viewmode-header">
            <div className="viewmode-info">
              <h3>Impact Intelligence Report</h3>
              <p>Switch between the simple developer takeaway view and deep technical AST call graph inspection.</p>
            </div>

            <div className="mode-toggle-pill">
              <button
                type="button"
                className={`mode-btn ${viewMode === 'simple' ? 'active' : ''}`}
                onClick={() => setViewMode('simple')}
              >
                <Sparkles size={14} />
                <span>Simple View (Default)</span>
              </button>
              <button
                type="button"
                className={`mode-btn ${viewMode === 'technical' ? 'active' : ''}`}
                onClick={() => setViewMode('technical')}
              >
                <Code2 size={14} />
                <span>Technical View</span>
              </button>
            </div>
          </div>

          {viewMode === 'simple' ? (
            /* =========================================================================
               SIMPLE VIEW (DEFAULT)
               Clean, visual, actionable, minimal jargon
               ========================================================================= */
            <div className="simple-view-layout">
              {/* Section A: Analysis Overview */}
              <AnalysisOverviewCard
                report={report}
                repoName={activeRecord?.repo_name}
              />

              {/* Section B: What Changed? */}
              <WhatChangedSection report={report} />

              {/* Section C: What Could Be Affected? (Interactive Impact Map) */}
              <InteractiveImpactMap report={report} />

              {/* Section D: What Should I Test? */}
              <WhatToTestSection report={report} />

              {/* Section E: Understand the Risk */}
              <RiskExplanationCard report={report} />
            </div>
          ) : (
            /* =========================================================================
               TECHNICAL VIEW
               Deep AST symbols, line ranges, raw diffs, dependency edges, graph metrics
               ========================================================================= */
            <div className="technical-view-layout">
              {/* Technical Metrics Header */}
              <div className="surface-card technical-metrics-bar">
                <div className="tech-metric-item">
                  <span className="tech-metric-label">NetworkX AST Nodes</span>
                  <b className="tech-metric-val">{report.graph_nodes_count}</b>
                </div>
                <div className="tech-metric-item">
                  <span className="tech-metric-label">Dependency Edges</span>
                  <b className="tech-metric-val">{report.graph_edges_count}</b>
                </div>
                <div className="tech-metric-item">
                  <span className="tech-metric-label">Changed AST Symbols</span>
                  <b className="tech-metric-val">{report.changed_symbols.length}</b>
                </div>
                <div className="tech-metric-item">
                  <span className="tech-metric-label">Traversed Callers</span>
                  <b className="tech-metric-val">{report.impacted_symbols.length}</b>
                </div>
                <div className="tech-metric-item">
                  <span className="tech-metric-label">Targeted Test Symbols</span>
                  <b className="tech-metric-val">{report.recommended_tests.length}</b>
                </div>
              </div>

              {/* Deep AST Symbol Registry */}
              <section className="surface-card">
                <div className="card-heading">
                  <div>
                    <h3>1. AST Symbol Boundaries & Line Ranges</h3>
                    <p>Direct AST nodes intersecting modified Git diff hunks</p>
                  </div>
                  <span className="subtle-count">{report.changed_symbols.length} symbols</span>
                </div>

                <div className="symbol-table">
                  <div className="symbol-table-header">
                    <span>FULLY QUALIFIED SYMBOL ID</span>
                    <span>TYPE</span>
                    <span>FILE LOCATION</span>
                    <span>LINE BOUNDARIES</span>
                  </div>
                  {report.changed_symbols.map((sym) => (
                    <div key={sym.id} className="symbol-table-row modified-row">
                      <span className="symbol-name-col">
                        <Braces size={15} color="var(--lime)" />
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

              {/* Reverse Dependency Traversal Call Chains */}
              <section className="surface-card">
                <div className="card-heading">
                  <div>
                    <h3>2. Reverse Dependency Traversal & Call Chains</h3>
                    <p>Upstream consumers discovered by traversing the NetworkX call graph</p>
                  </div>
                  <span className="subtle-count">{report.impacted_symbols.length} callers</span>
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
                            {isDirectChange
                              ? 'DIRECT CHANGE'
                              : `DEPTH ${imp.depth}: ${imp.impact_type.toUpperCase()}`}
                          </span>
                          <span className="impact-file-tag">
                            {imp.file_path}:L{imp.line_start}
                          </span>
                        </div>
                        <div className="impact-node-body">
                          <b>{imp.symbol_name}</b>
                          <small className="impact-id-text">{imp.symbol_id}</small>
                        </div>
                        {imp.path_from_change.length > 1 && (
                          <div className="impact-path-breadcrumb">
                            <span>Traversal Chain:</span>
                            {imp.path_from_change.map((p, idx) => (
                              <span key={idx} className="path-step">
                                {idx > 0 && <span className="path-arrow">&rarr;</span>}
                                <code>{p}</code>
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </section>

              {/* Raw Git Diff Console */}
              {report.file_diffs && report.file_diffs.length > 0 && (
                <section className="surface-card">
                  <div className="card-heading">
                    <div>
                      <h3>3. Raw Git Diff Stream</h3>
                      <p>Unified diff hunks extracted between {report.base_commit.slice(0, 7)} and {report.head_commit.slice(0, 7)}</p>
                    </div>
                    <button
                      type="button"
                      className="button button-ghost button-small"
                      onClick={handleCopyRawDiff}
                    >
                      {copiedRawDiff ? (
                        <>
                          <Check size={14} color="var(--lime)" />
                          <span>Copied Diff</span>
                        </>
                      ) : (
                        <>
                          <Copy size={14} />
                          <span>Copy Raw Diff</span>
                        </>
                      )}
                    </button>
                  </div>

                  <div className="raw-diff-console">
                    <pre>
                      <code>
                        {report.file_diffs.map((f) => `--- ${f.file_path} (${f.change_type})\n${f.diff_content || 'No text diff'}`).join('\n\n')}
                      </code>
                    </pre>
                  </div>
                </section>
              )}
            </div>
          )}
        </div>
      ) : (
        /* Empty State */
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
