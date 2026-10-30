import React from 'react';
import {
  AlertTriangle,
  ArrowUpRight,
  GitPullRequest,
  Info,
  Layers,
  Scale,
  Shield,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
  Workflow,
} from 'lucide-react';
import { ImpactAnalysisReport } from '../../../types';

interface RiskExplanationCardProps {
  report: ImpactAnalysisReport;
}

export const RiskExplanationCard: React.FC<RiskExplanationCardProps> = ({ report }) => {
  const directDependents = report.impacted_symbols.filter((s) => s.depth === 1).length;
  const indirectDependents = report.impacted_symbols.filter((s) => s.depth >= 2).length;
  const maxDepth = report.impacted_symbols.reduce((max, s) => Math.max(max, s.depth), 0);

  // Determine factor weights
  const depthFactor = Math.min(100, maxDepth * 30);
  const callerFactor = Math.min(100, (directDependents * 15) + (indirectDependents * 10));
  const surfaceFactor = Math.min(100, report.changed_symbols.length * 25);

  const getRiskTag = (level: string) => {
    switch (level) {
      case 'high':
        return {
          icon: <ShieldAlert size={20} color="#d66e68" />,
          color: '#d66e68',
          title: 'High Ripple Exposure',
          summary:
            'This modification alters deeply embedded functions that multiple downstream features rely upon. Regression risk propagates across multiple architecture layers.',
        };
      case 'elevated':
        return {
          icon: <AlertTriangle size={20} color="#d9a15f" />,
          color: '#d9a15f',
          title: 'Elevated Downstream Impact',
          summary:
            'Changes propagate beyond the immediate module to affect connected services. Reviewing direct callers and executing recommended tests is strongly advised.',
        };
      case 'medium':
        return {
          icon: <Scale size={20} color="#e0b468" />,
          color: '#e0b468',
          title: 'Moderate Blast Radius',
          summary:
            'Changes touch intermediate functions with a moderate caller footprint. Targeted testing is sufficient to validate stability.',
        };
      default:
        return {
          icon: <ShieldCheck size={20} color="var(--lime)" />,
          color: 'var(--lime)',
          title: 'Localized Code Change',
          summary:
            'Minimal or no downstream callers are impacted by this change. The blast radius is tightly constrained to the altered file.',
        };
    }
  };

  const tag = getRiskTag(report.risk_level);

  return (
    <section className="surface-card risk-explanation-card">
      <div className="section-header-row">
        <div>
          <div className="section-eyebrow">
            <Shield size={14} color={tag.color} />
            <span>RISK INTELLIGENCE</span>
          </div>
          <h3>Understand the Risk</h3>
          <p>
            How ChangeRadar calculates change blast radius and what this score means for your pull request.
          </p>
        </div>

        <div className="risk-score-display" style={{ borderColor: tag.color }}>
          <div className="score-badge-circle" style={{ background: `${tag.color}20`, color: tag.color }}>
            {Math.round(report.risk_score)}
          </div>
          <div className="score-badge-meta">
            <b style={{ color: tag.color }}>{report.risk_level.toUpperCase()}</b>
            <small>Score out of 100</small>
          </div>
        </div>
      </div>

      <div className="risk-assessment-banner" style={{ borderLeftColor: tag.color }}>
        <div className="risk-banner-icon">{tag.icon}</div>
        <div className="risk-banner-content">
          <h4>{tag.title}</h4>
          <p>{tag.summary}</p>
        </div>
      </div>

      {/* Contributing Factors */}
      <div className="risk-factors-breakdown">
        <h4 className="factors-heading">Contributing Heuristic Factors:</h4>

        <div className="factors-grid">
          {/* Factor 1: Propagation Depth */}
          <div className="factor-box">
            <div className="factor-header">
              <span className="factor-name">Call Graph Depth</span>
              <span className="factor-value">{maxDepth} Levels Deep</span>
            </div>
            <div className="factor-bar-track">
              <div
                className="factor-bar-fill"
                style={{ width: `${depthFactor}%`, background: 'var(--amber)' }}
              />
            </div>
            <p className="factor-desc">
              Measures how many hops downstream the altered functions ripple. Deeper call chains increase the likelihood of unintended side effects.
            </p>
          </div>

          {/* Factor 2: Caller Volume */}
          <div className="factor-box">
            <div className="factor-header">
              <span className="factor-name">Downstream Caller Volume</span>
              <span className="factor-value">
                {directDependents + indirectDependents} Consumers
              </span>
            </div>
            <div className="factor-bar-track">
              <div
                className="factor-bar-fill"
                style={{ width: `${callerFactor}%`, background: 'var(--violet)' }}
              />
            </div>
            <p className="factor-desc">
              Number of functions, methods, and modules that import or call the modified components across the codebase.
            </p>
          </div>

          {/* Factor 3: Surface Alteration */}
          <div className="factor-box">
            <div className="factor-header">
              <span className="factor-name">Public API / Symbol Surface</span>
              <span className="factor-value">{report.changed_symbols.length} Altered Symbols</span>
            </div>
            <div className="factor-bar-track">
              <div
                className="factor-bar-fill"
                style={{ width: `${surfaceFactor}%`, background: 'var(--lime)' }}
              />
            </div>
            <p className="factor-desc">
              Scope of modified symbols. Modifying core utility or service entry points carries a higher blast radius than leaf implementations.
            </p>
          </div>
        </div>
      </div>

      {/* Explicit Heuristic Structural Disclaimer */}
      <div className="risk-disclaimer-box">
        <Info size={16} className="disclaimer-icon" />
        <div className="disclaimer-text">
          <b>Heuristic Structural Blast Radius — Not a Defect Probability</b>
          <p>
            ChangeRadar evaluates architectural reach and coupling via static AST parsing. A high score indicates broad structural dependency, not that the code is defective or broken. Use this index to focus code reviews and regression testing.
          </p>
        </div>
      </div>
    </section>
  );
};
