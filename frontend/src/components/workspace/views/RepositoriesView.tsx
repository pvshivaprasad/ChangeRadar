import { EmptyState } from '../../ui/EmptyState';
import { Github } from 'lucide-react';

export function RepositoriesView({ onConnect }: { onConnect: () => void }) {
  return (
    <section className="surface-card full-card">
      <div className="card-heading">
        <div>
          <h3>Your repositories</h3>
          <p>Repositories connected to this workspace</p>
        </div>
        <span className="subtle-count">0 repositories</span>
      </div>
      <EmptyState
        title="Your code belongs here"
        description="Connect a GitHub repository to scan its structure, map dependencies, and start analysing changes."
        action="Connect GitHub repository"
        onAction={onConnect}
        icon={<Github size={24} />}
      />
    </section>
  );
}
