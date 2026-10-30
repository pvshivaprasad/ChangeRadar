import React, { useMemo, useState } from 'react';
import {
  ArrowRight,
  Braces,
  Check,
  ChevronRight,
  Filter,
  Info,
  Layers,
  ListTree,
  Network,
  Search,
  Sparkles,
  Workflow,
  X,
} from 'lucide-react';
import { ImpactedSymbol, ImpactAnalysisReport } from '../../../types';

interface InteractiveImpactMapProps {
  report: ImpactAnalysisReport;
}

export const InteractiveImpactMap: React.FC<InteractiveImpactMapProps> = ({ report }) => {
  const [viewMode, setViewMode] = useState<'visual' | 'list'>('visual');
  const [searchQuery, setSearchQuery] = useState('');
  const [depthFilter, setDepthFilter] = useState<'all' | 'direct' | 'transitive'>('all');
  const [selectedSymbolId, setSelectedSymbolId] = useState<string | null>(null);

  // Partition symbols by depth
  const rootSymbols = report.impacted_symbols.filter((s) => s.depth === 0);
  const directSymbols = report.impacted_symbols.filter((s) => s.depth === 1);
  const transitiveSymbols = report.impacted_symbols.filter((s) => s.depth >= 2);

  // Apply search & depth filtering
  const filteredSymbols = useMemo(() => {
    return report.impacted_symbols.filter((s) => {
      // Depth filter
      if (depthFilter === 'direct' && s.depth !== 1) return false;
      if (depthFilter === 'transitive' && s.depth < 2) return false;

      // Search filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchName = s.symbol_name.toLowerCase().includes(q);
        const matchId = s.symbol_id.toLowerCase().includes(q);
        const matchFile = s.file_path.toLowerCase().includes(q);
        return matchName || matchId || matchFile;
      }
      return true;
    });
  }, [report.impacted_symbols, depthFilter, searchQuery]);

  // Find currently selected symbol for click-to-inspect evidence panel
  const selectedSymbol = useMemo(() => {
    if (!selectedSymbolId) {
      // Default select the first impacted caller if available
      return directSymbols[0] || transitiveSymbols[0] || rootSymbols[0] || null;
    }
    return report.impacted_symbols.find((s) => s.symbol_id === selectedSymbolId) || null;
  }, [selectedSymbolId, report.impacted_symbols, directSymbols, transitiveSymbols, rootSymbols]);

  const getDepthLabel = (depth: number) => {
    if (depth === 0) return 'Root Change';
    if (depth === 1) return 'Direct Dependent (1 hop)';
    return `Indirect Dependent (${depth} hops)`;
  };

  const getDepthPillClass = (depth: number) => {
    if (depth === 0) return 'impact-pill-root';
    if (depth === 1) return 'impact-pill-direct';
    return 'impact-pill-transitive';
  };

  return (
    <section className="surface-card impact-map-card">
      <div className="section-header-row">
        <div>
          <div className="section-eyebrow">
            <Workflow size={14} color="var(--amber)" />
            <span>DEPENDENCY BLAST RADIUS</span>
          </div>
          <h3>What Could Be Affected?</h3>
          <p>
            Interactive dependency map showing how changes ripple through your codebase. Click any
            component to inspect its causal path.
          </p>
        </div>

        {/* View Toggle (Visual vs List) */}
        <div className="impact-view-controls">
          <div className="mode-toggle-group">
            <button
              type="button"
              className={`toggle-option ${viewMode === 'visual' ? 'active' : ''}`}
              onClick={() => setViewMode('visual')}
              title="Interactive Visual DAG"
            >
              <Network size={14} />
              <span>Visual Map</span>
            </button>
            <button
              type="button"
              className={`toggle-option ${viewMode === 'list' ? 'active' : ''}`}
              onClick={() => setViewMode('list')}
              title="Accessible Detailed List"
            >
              <ListTree size={14} />
              <span>Detailed List</span>
            </button>
          </div>
        </div>
      </div>

      {/* Toolbar: Depth Filter & Search */}
      <div className="impact-toolbar">
        <div className="depth-filter-pills">
          <button
            type="button"
            className={`depth-filter-btn ${depthFilter === 'all' ? 'active' : ''}`}
            onClick={() => setDepthFilter('all')}
          >
            All Components ({report.impacted_symbols.length})
          </button>
          <button
            type="button"
            className={`depth-filter-btn ${depthFilter === 'direct' ? 'active' : ''}`}
            onClick={() => setDepthFilter('direct')}
          >
            <span className="dot-indicator dot-direct" />
            Direct Dependents ({directSymbols.length})
          </button>
          <button
            type="button"
            className={`depth-filter-btn ${depthFilter === 'transitive' ? 'active' : ''}`}
            onClick={() => setDepthFilter('transitive')}
          >
            <span className="dot-indicator dot-transitive" />
            Indirect Ripple ({transitiveSymbols.length})
          </button>
        </div>

        <div className="impact-search-box">
          <Search size={14} />
          <input
            type="text"
            placeholder="Search affected functions, classes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <button type="button" onClick={() => setSearchQuery('')} className="clear-search-btn">
              <X size={12} />
            </button>
          )}
        </div>
      </div>

      {/* Main Impact Body */}
      {viewMode === 'visual' ? (
        <div className="visual-dag-layout">
          {/* 3-Column Visual Flow */}
          <div className="visual-columns-container">
            {/* Column 1: Root Changes */}
            <div className="dag-column root-column">
              <div className="dag-column-header">
                <span className="dag-column-badge badge-root">STARTING POINT</span>
                <h4>Modified Code</h4>
                <small>{rootSymbols.length} root symbol{rootSymbols.length !== 1 ? 's' : ''}</small>
              </div>

              <div className="dag-nodes-list">
                {rootSymbols.map((sym) => {
                  const isSelected = selectedSymbol?.symbol_id === sym.symbol_id;
                  return (
                    <div
                      key={sym.symbol_id}
                      className={`dag-node-card root-node ${isSelected ? 'selected' : ''}`}
                      onClick={() => setSelectedSymbolId(sym.symbol_id)}
                      role="button"
                      tabIndex={0}
                    >
                      <div className="node-badge-row">
                        <span className="node-type-tag">{sym.symbol_type}</span>
                        <span className="node-location">{sym.file_path.split('/').pop()}:L{sym.line_start}</span>
                      </div>
                      <div className="node-name-row">
                        <Braces size={15} color="var(--lime)" />
                        <b>{sym.symbol_name}</b>
                      </div>
                      <div className="node-hint">Root change origin &rarr;</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Connecting Flow Arrow 1 */}
            <div className="dag-flow-divider">
              <div className="flow-line" />
              <div className="flow-badge">Direct calls</div>
              <ArrowRight size={18} className="flow-arrow-icon" />
            </div>

            {/* Column 2: Direct Dependents */}
            <div className="dag-column direct-column">
              <div className="dag-column-header">
                <span className="dag-column-badge badge-direct">LEVEL 1 DEPENDENTS</span>
                <h4>Direct Callers</h4>
                <small>{directSymbols.length} direct consumer{directSymbols.length !== 1 ? 's' : ''}</small>
              </div>

              <div className="dag-nodes-list">
                {directSymbols.length === 0 ? (
                  <div className="empty-column-notice">No direct callers detected.</div>
                ) : (
                  directSymbols.map((sym) => {
                    const isSelected = selectedSymbol?.symbol_id === sym.symbol_id;
                    return (
                      <div
                        key={sym.symbol_id}
                        className={`dag-node-card direct-node ${isSelected ? 'selected' : ''}`}
                        onClick={() => setSelectedSymbolId(sym.symbol_id)}
                        role="button"
                        tabIndex={0}
                      >
                        <div className="node-badge-row">
                          <span className="node-type-tag tag-direct">{sym.symbol_type}</span>
                          <span className="node-location">{sym.file_path.split('/').pop()}:L{sym.line_start}</span>
                        </div>
                        <div className="node-name-row">
                          <Workflow size={15} color="var(--amber)" />
                          <b>{sym.symbol_name}</b>
                        </div>
                        <div className="node-path-peek">
                          Directly invokes altered symbol
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Connecting Flow Arrow 2 */}
            <div className="dag-flow-divider">
              <div className="flow-line" />
              <div className="flow-badge">Transitive ripple</div>
              <ArrowRight size={18} className="flow-arrow-icon" />
            </div>

            {/* Column 3: Transitive Dependents */}
            <div className="dag-column transitive-column">
              <div className="dag-column-header">
                <span className="dag-column-badge badge-transitive">LEVEL 2+ RIPPLE</span>
                <h4>Indirect Callers</h4>
                <small>{transitiveSymbols.length} indirect consumer{transitiveSymbols.length !== 1 ? 's' : ''}</small>
              </div>

              <div className="dag-nodes-list">
                {transitiveSymbols.length === 0 ? (
                  <div className="empty-column-notice">
                    No downstream ripple callers beyond direct level.
                  </div>
                ) : (
                  transitiveSymbols.map((sym) => {
                    const isSelected = selectedSymbol?.symbol_id === sym.symbol_id;
                    return (
                      <div
                        key={sym.symbol_id}
                        className={`dag-node-card transitive-node ${isSelected ? 'selected' : ''}`}
                        onClick={() => setSelectedSymbolId(sym.symbol_id)}
                        role="button"
                        tabIndex={0}
                      >
                        <div className="node-badge-row">
                          <span className="node-type-tag tag-transitive">
                            Depth {sym.depth}
                          </span>
                          <span className="node-location">{sym.file_path.split('/').pop()}:L{sym.line_start}</span>
                        </div>
                        <div className="node-name-row">
                          <Workflow size={15} color="var(--violet)" />
                          <b>{sym.symbol_name}</b>
                        </div>
                        <div className="node-path-peek">
                          {sym.depth} hops away from change
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          {/* Click-to-Inspect Evidence Panel */}
          {selectedSymbol && (
            <div className="causal-evidence-panel">
              <div className="evidence-panel-header">
                <div className="evidence-title">
                  <span className={`evidence-badge ${getDepthPillClass(selectedSymbol.depth)}`}>
                    {getDepthLabel(selectedSymbol.depth)}
                  </span>
                  <h4>
                    Causal Evidence: <code>{selectedSymbol.symbol_name}</code>
                  </h4>
                </div>
                <div className="evidence-meta">
                  <span>{selectedSymbol.file_path}:L{selectedSymbol.line_start}-L{selectedSymbol.line_end}</span>
                </div>
              </div>

              <div className="evidence-body">
                <div className="evidence-explainer">
                  <p>
                    {selectedSymbol.depth === 0 ? (
                      <>This symbol was directly modified in the commit diff. It serves as the root origin of downstream ripple effects.</>
                    ) : selectedSymbol.depth === 1 ? (
                      <>This component directly calls or imports the modified symbol. Any changes in signature, return contract, or behavior directly impact this code path.</>
                    ) : (
                      <>This component is affected transitively ({selectedSymbol.depth} call hops away). A regression in the root change can propagate upstream through intermediate functions to impact this component.</>
                    )}
                  </p>
                </div>

                {/* Step-by-Step Causal Call Chain */}
                <div className="causal-chain-box">
                  <span className="chain-box-label">Verified AST Causal Chain:</span>
                  <div className="causal-chain-steps">
                    {selectedSymbol.path_from_change.map((step, idx) => {
                      const isRoot = idx === 0;
                      const isTarget = idx === selectedSymbol.path_from_change.length - 1;
                      const stepParts = step.split('.');
                      const shortName = stepParts.slice(-2).join('.');

                      return (
                        <div key={idx} className="chain-step-item">
                          {idx > 0 && (
                            <div className="chain-arrow-sep">
                              <ArrowRight size={14} />
                              <span className="chain-arrow-label">calls</span>
                            </div>
                          )}
                          <div
                            className={`chain-step-pill ${
                              isRoot ? 'pill-root' : isTarget ? 'pill-target' : 'pill-intermediate'
                            }`}
                          >
                            <span className="step-num">{idx + 1}</span>
                            <span className="step-name">{shortName}</span>
                            <small className="step-full-id">{step}</small>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Accessible Detailed List View Alternative */
        <div className="accessible-impact-list">
          <div className="list-view-header">
            <span>COMPONENT</span>
            <span>BLAST RADIUS DEPTH</span>
            <span>LOCATION</span>
            <span>CAUSAL PATH FROM ROOT</span>
          </div>

          {filteredSymbols.map((sym) => (
            <div
              key={sym.symbol_id}
              className={`impact-list-row ${selectedSymbol?.symbol_id === sym.symbol_id ? 'active-row' : ''}`}
              onClick={() => setSelectedSymbolId(sym.symbol_id)}
            >
              <div className="list-col-name">
                <Braces size={14} color="var(--lime)" />
                <div>
                  <b>{sym.symbol_name}</b>
                  <small>{sym.symbol_id}</small>
                </div>
              </div>

              <div className="list-col-depth">
                <span className={`depth-badge-sm ${getDepthPillClass(sym.depth)}`}>
                  {sym.depth === 0 ? 'Direct Change' : `Depth ${sym.depth}`}
                </span>
              </div>

              <div className="list-col-location">
                <code>{sym.file_path}:L{sym.line_start}</code>
              </div>

              <div className="list-col-chain">
                {sym.path_from_change.map((p, idx) => (
                  <span key={idx} className="chain-mini-step">
                    {idx > 0 && <span className="mini-arrow">&rarr;</span>}
                    <code>{p.split('.').pop()}</code>
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
};
