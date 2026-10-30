import { EmptyState } from '../../ui/EmptyState';
import { Check } from 'lucide-react';

export function TestsView() {
  return (
    <section className="surface-card full-card">
      <div className="card-heading">
        <div>
          <h3>Test intelligence</h3>
          <p>Prioritized test suggestions based on changed code paths.</p>
        </div>
        <span className="subtle-count">No recommendations</span>
      </div>
      <EmptyState
        title="No test insights yet"
        description="Run an impact analysis to discover relevant tests and surface potential coverage gaps across your suite."
        icon={<Check size={24} />}
      />
    </section>
  );
}
