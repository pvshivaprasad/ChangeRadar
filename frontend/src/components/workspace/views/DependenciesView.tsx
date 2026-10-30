import { useState, useMemo } from 'react';
import {
  Boxes,
  Braces,
  Filter,
  Layers,
  Play,
  RotateCcw,
  Search,
  Workflow,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';
import { EmptyState } from '../../ui/EmptyState';
import { ScanSummary } from '../../../types';

interface DependenciesViewProps {
  scan: ScanSummary | null;
  onScanSample: () => void;
  isLoading: boolean;
}

export function DependenciesView({
  scan,
  onScanSample,
  isLoading,
}: DependenciesViewProps) {
  const [query, setQuery] = useState('');
  const [filterType, setFilterType] = useState<string>('all');

  const symbols = scan?.symbols || [];

  const filteredSymbols = useMemo(() => {
    return symbols.filter((s) => {
      const matchesQuery =
        !query ||
        s.name.toLowerCase().includes(query.toLowerCase()) ||
        s.id.toLowerCase().includes(query.toLowerCase()) ||
        s.file_path.toLowerCase().includes(query.toLowerCase());

      const matchesType =
        filterType === 'all' || s.symbol_type.toLowerCase() === filterType.toLowerCase();

      return matchesQuery && matchesType;
    });
  }, [symbols, query, filterType]);

  const typeCounts = useMemo(() => {
    const counts = { all: symbols.length, module: 0, class: 0, function: 0, method: 0 };
    for (const s of symbols) {
      if (s.symbol_type in counts) {
        counts[s.symbol_type as keyof typeof counts]++;
      }
    }
    return counts;
  }, [symbols]);

  return (
    <div className="view-container">
      {/* Explorer Controls Toolbar */}
      <div className="surface-card toolbar-card">
        <div className="toolbar-left">
          <div className="search-input-wrap">
            <Search size={15} />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filter symbols (e.g. AuthService or process_payment)..."
            />
          </div>
          <div className="filter-chips">
            <button
              className={`chip ${filterType === 'all' ? 'chip-active' : ''}`}
              onClick={() => setFilterType('all')}
              type="button"
            >
              All ({typeCounts.all})
            </button>
            <button
              className={`chip ${filterType === 'class' ? 'chip-active' : ''}`}
              onClick={() => setFilterType('class')}
              type="button"
            >
              Classes ({typeCounts.class})
            </button>
            <button
              className={`chip ${filterType === 'method' ? 'chip-active' : ''}`}
              onClick={() => setFilterType('method')}
              type="button"
            >
              Methods ({typeCounts.method})
            </button>
            <button
              className={`chip ${filterType === 'function' ? 'chip-active' : ''}`}
              onClick={() => setFilterType('function')}
              type="button"
            >
              Functions ({typeCounts.function})
            </button>
            <button
              className={`chip ${filterType === 'module' ? 'chip-active' : ''}`}
              onClick={() => setFilterType('module')}
              type="button"
            >
              Modules ({typeCounts.module})
            </button>
          </div>
        </div>

        <div className="toolbar-right">
          <button
            className="button button-lime button-small"
            onClick={onScanSample}
            disabled={isLoading}
            type="button"
          >
            <Play size={14} />
            <span>{isLoading ? 'Scanning...' : 'Scan Sample Code Map'}</span>
          </button>
        </div>
      </div>

      {/* Main Symbols & Graph DAG List */}
      <section className="surface-card full-card">
        <div className="card-heading">
          <div>
            <h3>AST Symbol Registry & Provenance</h3>
            <p>
              {scan
                ? `Mapped ${scan.symbol_count} AST symbols and ${scan.edge_count} dependency edges across ${scan.file_count} files`
                : 'Visual DAG representation of function calls, class inheritances, and cross-file imports'}
            </p>
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

        {scan && filteredSymbols.length > 0 ? (
          <div className="symbol-registry-list">
            <div className="symbol-table-header">
              <span>AST SYMBOL</span>
              <span>TYPE</span>
              <span>FILE PATH</span>
              <span>SOURCE LOCATION</span>
            </div>
            {filteredSymbols.map((sym) => (
              <div key={sym.id} className="symbol-table-row">
                <span className="symbol-name-col">
                  {sym.symbol_type === 'class' ? (
                    <Boxes size={15} color="#d9a15f" />
                  ) : sym.symbol_type === 'method' ? (
                    <Braces size={15} color="#8bb736" />
                  ) : sym.symbol_type === 'function' ? (
                    <Workflow size={15} color="#a69bea" />
                  ) : (
                    <Layers size={15} color="#8c9584" />
                  )}
                  <b>{sym.name}</b>
                  <small>{sym.id}</small>
                </span>
                <span className="symbol-badge">{sym.symbol_type.toUpperCase()}</span>
                <span className="symbol-file-col">{sym.file_path}</span>
                <span className="symbol-lines-col">Lines {sym.line_start}–{sym.line_end}</span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            title="Dependency graph unpopulated"
            description="Click 'Scan Sample Code Map' above to extract and inspect the complete AST symbol table and import relationships from our verified test fixture."
            action="Scan Sample Codebase"
            onAction={onScanSample}
            icon={<Workflow size={28} />}
          />
        )}
      </section>
    </div>
  );
}
