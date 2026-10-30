import { Check, CheckCircle2, Clock, Filter, Search, Sparkles } from 'lucide-react';
import { EmptyState } from '../../ui/EmptyState';

export function TestsView() {
  return (
    <div className="view-container">
      {/* Test Metric Stats */}
      <div className="metric-grid test-metric-grid">
        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Targeted Tests</span>
            <CheckCircle2 size={18} className="metric-icon" />
          </div>
          <strong className="metric-value">—</strong>
          <span className="metric-subtext">Tests touching changed AST paths</span>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Safe to Skip</span>
            <Sparkles size={18} className="metric-icon" />
          </div>
          <strong className="metric-value">—</strong>
          <span className="metric-subtext">Zero downstream dependency touch</span>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Estimated Time Saved</span>
            <Clock size={18} className="metric-icon" />
          </div>
          <strong className="metric-value">—</strong>
          <span className="metric-subtext">CI runtime reduction</span>
        </div>
      </div>

      <section className="surface-card full-card">
        <div className="card-heading">
          <div>
            <h3>Targeted Test Recommendations</h3>
            <p>Prioritized test files selected by mapping AST call graphs from changed symbols</p>
          </div>
          <span className="subtle-count">0 tests recommended</span>
        </div>

        <EmptyState
          title="No test insights yet"
          description="Run an impact analysis between two commits to discover relevant test suites and identify untested modified paths."
          icon={<Check size={28} />}
        />
      </section>
    </div>
  );
}
