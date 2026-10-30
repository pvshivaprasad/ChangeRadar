import { EmptyState } from '../../ui/EmptyState';
import { Workflow } from 'lucide-react';

export function DependenciesView() {
  return (
    <section className="surface-card full-card">
      <div className="card-heading">
        <div>
          <h3>Dependency explorer</h3>
          <p>Navigate module, class, and function relationships.</p>
        </div>
        <span className="subtle-count">No graph generated</span>
      </div>
      <EmptyState
        title="Your code map starts here"
        description="Once a repository has been scanned, its dependency graph will become explorable here with full AST symbol extraction."
        icon={<Workflow size={24} />}
      />
    </section>
  );
}
