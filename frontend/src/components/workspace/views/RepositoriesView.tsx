import { Github, Plus, ShieldCheck } from 'lucide-react';
import { EmptyState } from '../../ui/EmptyState';

export function RepositoriesView({ onConnect }: { onConnect: () => void }) {
  return (
    <div className="view-container">
      <section className="surface-card full-card">
        <div className="card-heading">
          <div>
            <h3>Connected Codebases</h3>
            <p>Repositories monitored for AST change detection and dependency mapping</p>
          </div>
          <button
            className="button button-lime button-small"
            onClick={onConnect}
            type="button"
          >
            <Plus size={16} /> Connect repository
          </button>
        </div>

        <EmptyState
          title="Your code belongs here"
          description="Connect a GitHub repository to scan its file structure, extract symbol hierarchies, and start analyzing pull requests."
          action="Connect GitHub repository"
          onAction={onConnect}
          icon={<Github size={28} />}
        />

        <div className="security-banner">
          <ShieldCheck size={16} />
          <span>
            <b>Zero Code Execution Policy:</b> ChangeRadar performs pure static AST parsing.
            Untrusted code is never imported, invoked, or executed in any environment.
          </span>
        </div>
      </section>
    </div>
  );
}
