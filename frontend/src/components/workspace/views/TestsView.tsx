import { Check, CheckCircle2, Clock, Filter, Play, Search, ShieldCheck, Sparkles } from 'lucide-react';
import { EmptyState } from '../../ui/EmptyState';
import { ImpactAnalysisReport } from '../../../types';

interface TestsViewProps {
  report: ImpactAnalysisReport | null;
  onRunSample: () => void;
  isLoading: boolean;
}

export function TestsView({ report, onRunSample, isLoading }: TestsViewProps) {
  const hasData = report !== null;
  const tests = report?.recommended_tests || [];

  return (
    <div className="view-container">
      {/* Test Metric Stats */}
      <div className="metric-grid test-metric-grid">
        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Targeted Tests Recommended</span>
            <CheckCircle2 size={18} className="metric-icon" />
          </div>
          <strong className="metric-value">{hasData ? tests.length : '—'}</strong>
          <span className="metric-subtext">
            {hasData ? 'Directly traverses changed AST code paths' : 'Waiting for change analysis'}
          </span>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">High Priority Suites</span>
            <Sparkles size={18} className="metric-icon" />
          </div>
          <strong className="metric-value">
            {hasData ? tests.filter((t) => t.priority === 'high').length : '—'}
          </strong>
          <span className="metric-subtext">
            {hasData ? 'Direct tests of modified functions' : 'Zero downstream dependency touch'}
          </span>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Covered Altered Paths</span>
            <Clock size={18} className="metric-icon" />
          </div>
          <strong className="metric-value">
            {hasData ? `${new Set(tests.map((t) => t.target_symbol_id)).size} of ${report.changed_symbols.length}` : '—'}
          </strong>
          <span className="metric-subtext">
            {hasData ? 'Direct modified symbols with targeted tests' : 'Targeted test coverage'}
          </span>
        </div>
      </div>

      <section className="surface-card full-card">
        <div className="card-heading">
          <div>
            <h3>Targeted Test Recommendations</h3>
            <p>Prioritized test files selected by mapping AST call graphs from changed symbols</p>
          </div>
          <span className="subtle-count">
            {hasData ? `${tests.length} tests recommended` : '0 tests recommended'}
          </span>
        </div>

        {hasData && tests.length > 0 ? (
          <div className="recommended-tests-list">
            <div className="test-table-header">
              <span>TEST FILE & CASE</span>
              <span>PRIORITY</span>
              <span>TARGET SYMBOL</span>
              <span>DETERMINISTIC REASONING</span>
            </div>
            {tests.map((rec, idx) => (
              <div key={idx} className="test-table-row">
                <span className="test-name-col">
                  <CheckCircle2 size={16} color="#8bb736" />
                  <div>
                    <b>{rec.test_symbol_id ? rec.test_symbol_id.split('.').pop() : rec.test_file}</b>
                    <small>{rec.test_file}</small>
                  </div>
                </span>
                <span className={`priority-badge priority-${rec.priority}`}>
                  {rec.priority.toUpperCase()}
                </span>
                <span className="test-target-col">
                  <code>{rec.target_symbol_id.split('.').slice(-2).join('.')}</code>
                </span>
                <span className="test-reason-col">{rec.reason}</span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No test insights yet"
            description="Run a change impact analysis to discover which specific tests exercise modified functions and downstream consumers."
            action="Run Sample Analysis"
            onAction={onRunSample}
            icon={<Check size={28} />}
          />
        )}
      </section>
    </div>
  );
}
