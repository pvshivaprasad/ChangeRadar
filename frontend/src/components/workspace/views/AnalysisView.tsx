import { EmptyState } from '../../ui/EmptyState';
import { GitBranch } from 'lucide-react';

export function AnalysisView({ onNavigate }: { onNavigate: () => void }) {
  return (
    <section className="surface-card full-card">
      <div className="card-heading">
        <div>
          <h3>Change analysis</h3>
          <p>Compare a base revision with a proposed change.</p>
        </div>
        <span className="status-pill">
          <i /> READY WHEN YOU ARE
        </span>
      </div>
      <EmptyState
        title="No repository selected"
        description="Connect a repository first. Then select a commit or pull request to generate an evidence-backed impact report."
        action="Go to repositories"
        onAction={onNavigate}
        icon={<GitBranch size={24} />}
      />
    </section>
  );
}
