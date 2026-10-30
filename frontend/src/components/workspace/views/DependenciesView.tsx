import { Filter, Search, Workflow, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';
import { EmptyState } from '../../ui/EmptyState';

export function DependenciesView() {
  return (
    <div className="view-container">
      {/* Explorer Controls Toolbar */}
      <div className="surface-card toolbar-card">
        <div className="toolbar-left">
          <div className="search-input-wrap">
            <Search size={15} />
            <input
              type="text"
              placeholder="Search symbol (e.g. auth.service or CheckoutHandler)..."
            />
          </div>
          <div className="filter-chips">
            <button className="chip chip-active" type="button">All (0)</button>
            <button className="chip" type="button">Modules</button>
            <button className="chip" type="button">Classes</button>
            <button className="chip" type="button">Functions</button>
          </div>
        </div>

        <div className="toolbar-right">
          <div className="graph-controls">
            <button className="icon-button" title="Zoom in" type="button">
              <ZoomIn size={16} />
            </button>
            <button className="icon-button" title="Zoom out" type="button">
              <ZoomOut size={16} />
            </button>
            <button className="icon-button" title="Reset view" type="button">
              <RotateCcw size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Canvas View */}
      <section className="surface-card full-card">
        <div className="card-heading">
          <div>
            <h3>Interactive Dependency Explorer</h3>
            <p>Visual DAG representation of function calls, class inheritances, and cross-file imports</p>
          </div>
          <div className="provenance-legend">
            <span className="legend-item">
              <i className="legend-dot dot-static" /> Confirmed Static Edge
            </span>
            <span className="legend-item">
              <i className="legend-dot dot-inferred" /> Inferred / Dynamic Edge
            </span>
          </div>
        </div>

        <EmptyState
          title="Dependency graph unpopulated"
          description="Once a repository revision is scanned, its complete symbol call graph will render here with interactive node exploration and path tracing."
          icon={<Workflow size={28} />}
        />
      </section>
    </div>
  );
}
