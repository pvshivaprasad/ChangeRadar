import { EmptyState } from '../../ui/EmptyState';
import { Activity } from 'lucide-react';

export function ReportsView() {
  return (
    <section className="surface-card full-card">
      <div className="card-heading">
        <div>
          <h3>Risk reports</h3>
          <p>Review previous impact assessments and traceable evidence.</p>
        </div>
        <span className="subtle-count">0 reports</span>
      </div>
      <EmptyState
        title="Your reports will live here"
        description="Every completed analysis will create a reproducible report tied directly to base and head commit SHAs."
        icon={<Activity size={24} />}
      />
    </section>
  );
}
