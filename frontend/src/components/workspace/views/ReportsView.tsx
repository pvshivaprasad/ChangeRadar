import { Activity, Calendar, Download, GitCommitHorizontal, ShieldAlert } from 'lucide-react';
import { EmptyState } from '../../ui/EmptyState';

export function ReportsView() {
  return (
    <div className="view-container">
      <section className="surface-card full-card">
        <div className="card-heading">
          <div>
            <h3>Audit & Impact Risk Reports</h3>
            <p>Reproducible change assessments linked to immutable Git commit SHAs</p>
          </div>
          <span className="subtle-count">0 reports generated</span>
        </div>

        <div className="reports-table-preview">
          <div className="table-header">
            <span>COMMIT SHA</span>
            <span>BASE REVISION</span>
            <span>AFFECTED SYMBOLS</span>
            <span>RISK LEVEL</span>
            <span>GENERATED AT</span>
          </div>

          <EmptyState
            title="Your historical reports will live here"
            description="Every completed analysis creates a permanent, evidence-backed audit report detailing downstream ripple effects."
            icon={<Activity size={28} />}
          />
        </div>
      </section>
    </div>
  );
}
