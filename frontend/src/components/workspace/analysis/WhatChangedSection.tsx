import React, { useState } from 'react';
import {
  Braces,
  ChevronDown,
  ChevronRight,
  FileCode,
  FileDiff as FileDiffIcon,
  FilePlus,
  FileText,
  FileX,
  Filter,
  Search,
} from 'lucide-react';
import { AstSymbol, FileDiff, ImpactAnalysisReport } from '../../../types';

interface WhatChangedSectionProps {
  report: ImpactAnalysisReport;
}

export const WhatChangedSection: React.FC<WhatChangedSectionProps> = ({ report }) => {
  const [filterType, setFilterType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [expandedFiles, setExpandedFiles] = useState<Record<string, boolean>>({});

  const toggleFile = (filePath: string) => {
    setExpandedFiles((prev) => ({
      ...prev,
      [filePath]: !prev[filePath],
    }));
  };

  const expandAll = () => {
    const next: Record<string, boolean> = {};
    const files = report.file_diffs && report.file_diffs.length > 0
      ? report.file_diffs.map((f) => f.file_path)
      : report.changed_files;
    files.forEach((f) => {
      next[f] = true;
    });
    setExpandedFiles(next);
  };

  const collapseAll = () => {
    setExpandedFiles({});
  };

  // Compile file list with metadata (either from file_diffs if available or changed_files)
  interface DisplayFile {
    filePath: string;
    changeType: 'added' | 'modified' | 'deleted' | 'renamed';
    oldPath?: string | null;
    additions: number;
    deletions: number;
    diffContent?: string;
    symbols: AstSymbol[];
  }

  const fileMap = new Map<string, DisplayFile>();

  if (report.file_diffs && report.file_diffs.length > 0) {
    report.file_diffs.forEach((fd) => {
      const syms = report.changed_symbols.filter(
        (s) => s.file_path.replace(/\\/g, '/') === fd.file_path.replace(/\\/g, '/')
      );
      fileMap.set(fd.file_path, {
        filePath: fd.file_path,
        changeType: (fd.change_type as any) || 'modified',
        oldPath: fd.old_path,
        additions: fd.additions,
        deletions: fd.deletions,
        diffContent: fd.diff_content,
        symbols: syms,
      });
    });
  } else {
    report.changed_files.forEach((cf) => {
      const syms = report.changed_symbols.filter(
        (s) => s.file_path.replace(/\\/g, '/') === cf.replace(/\\/g, '/')
      );
      fileMap.set(cf, {
        filePath: cf,
        changeType: 'modified',
        additions: 0,
        deletions: 0,
        symbols: syms,
      });
    });
  }

  const allFiles = Array.from(fileMap.values());

  const filteredFiles = allFiles.filter((f) => {
    if (filterType !== 'all' && f.changeType !== filterType) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchPath = f.filePath.toLowerCase().includes(q);
      const matchSym = f.symbols.some((s) => s.name.toLowerCase().includes(q) || s.id.toLowerCase().includes(q));
      return matchPath || matchSym;
    }
    return true;
  });

  const counts = {
    all: allFiles.length,
    modified: allFiles.filter((f) => f.changeType === 'modified').length,
    added: allFiles.filter((f) => f.changeType === 'added').length,
    deleted: allFiles.filter((f) => f.changeType === 'deleted').length,
    renamed: allFiles.filter((f) => f.changeType === 'renamed').length,
  };

  const renderBadge = (type: string) => {
    switch (type) {
      case 'added':
        return <span className="diff-pill diff-pill-added">Added</span>;
      case 'deleted':
        return <span className="diff-pill diff-pill-deleted">Deleted</span>;
      case 'renamed':
        return <span className="diff-pill diff-pill-renamed">Renamed</span>;
      default:
        return <span className="diff-pill diff-pill-modified">Modified</span>;
    }
  };

  const renderDiffLine = (line: string, idx: number) => {
    if (line.startsWith('@@')) {
      return (
        <div key={idx} className="diff-line diff-line-hunk">
          <span className="diff-line-gutter">...</span>
          <span className="diff-line-code">{line}</span>
        </div>
      );
    }
    if (line.startsWith('+')) {
      return (
        <div key={idx} className="diff-line diff-line-add">
          <span className="diff-line-gutter">+</span>
          <span className="diff-line-code">{line.slice(1)}</span>
        </div>
      );
    }
    if (line.startsWith('-')) {
      return (
        <div key={idx} className="diff-line diff-line-del">
          <span className="diff-line-gutter">-</span>
          <span className="diff-line-code">{line.slice(1)}</span>
        </div>
      );
    }
    return (
      <div key={idx} className="diff-line diff-line-ctx">
        <span className="diff-line-gutter">&nbsp;</span>
        <span className="diff-line-code">{line.startsWith(' ') ? line.slice(1) : line}</span>
      </div>
    );
  };

  return (
    <section className="surface-card what-changed-card">
      <div className="section-header-row">
        <div>
          <div className="section-eyebrow">
            <FileDiffIcon size={14} color="var(--lime)" />
            <span>CODE MODIFICATIONS</span>
          </div>
          <h3>What Changed?</h3>
          <p>Inspect files, functions, and classes altered in this commit revision.</p>
        </div>
        <div className="section-actions-row">
          <button type="button" className="action-link-btn" onClick={expandAll}>
            Expand All Diffs
          </button>
          <span className="action-sep">&bull;</span>
          <button type="button" className="action-link-btn" onClick={collapseAll}>
            Collapse All
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="diff-filter-toolbar">
        <div className="diff-type-tabs">
          <button
            type="button"
            className={`type-tab ${filterType === 'all' ? 'active' : ''}`}
            onClick={() => setFilterType('all')}
          >
            All Files ({counts.all})
          </button>
          {counts.modified > 0 && (
            <button
              type="button"
              className={`type-tab ${filterType === 'modified' ? 'active' : ''}`}
              onClick={() => setFilterType('modified')}
            >
              Modified ({counts.modified})
            </button>
          )}
          {counts.added > 0 && (
            <button
              type="button"
              className={`type-tab ${filterType === 'added' ? 'active' : ''}`}
              onClick={() => setFilterType('added')}
            >
              Added ({counts.added})
            </button>
          )}
          {counts.deleted > 0 && (
            <button
              type="button"
              className={`type-tab ${filterType === 'deleted' ? 'active' : ''}`}
              onClick={() => setFilterType('deleted')}
            >
              Deleted ({counts.deleted})
            </button>
          )}
          {counts.renamed > 0 && (
            <button
              type="button"
              className={`type-tab ${filterType === 'renamed' ? 'active' : ''}`}
              onClick={() => setFilterType('renamed')}
            >
              Renamed ({counts.renamed})
            </button>
          )}
        </div>

        <div className="diff-search-input">
          <Search size={14} />
          <input
            type="text"
            placeholder="Filter files or symbols..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Files List */}
      <div className="diff-files-container">
        {filteredFiles.length === 0 ? (
          <div className="empty-diff-placeholder">
            <span>No files match your filter query.</span>
          </div>
        ) : (
          filteredFiles.map((f) => {
            const isExpanded = !!expandedFiles[f.filePath];
            const hasDiff = f.diffContent && f.diffContent.trim().length > 0;

            return (
              <div key={f.filePath} className="diff-file-card">
                <div
                  className="diff-file-header"
                  onClick={() => toggleFile(f.filePath)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      toggleFile(f.filePath);
                    }
                  }}
                >
                  <div className="diff-file-title">
                    <span className="diff-toggle-arrow">
                      {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    </span>
                    <FileCode size={16} className="file-icon" />
                    <span className="file-path-text">{f.filePath}</span>
                    {f.oldPath && <span className="old-path-tag">&larr; was {f.oldPath}</span>}
                  </div>

                  <div className="diff-file-meta">
                    {f.additions > 0 && <span className="add-count">+{f.additions}</span>}
                    {f.deletions > 0 && <span className="del-count">-{f.deletions}</span>}
                    {renderBadge(f.changeType)}
                  </div>
                </div>

                {/* Changed Symbols Chips inside this file */}
                {f.symbols.length > 0 && (
                  <div className="file-symbols-strip">
                    <span className="symbols-strip-label">Altered Symbols:</span>
                    <div className="symbols-chips-wrap">
                      {f.symbols.map((sym) => (
                        <span key={sym.id} className="symbol-chip" title={sym.id}>
                          <Braces size={12} color="var(--lime)" />
                          <b>{sym.name}</b>
                          <small className="symbol-chip-type">({sym.symbol_type})</small>
                          <span className="symbol-chip-lines">
                            L{sym.line_start}-{sym.line_end}
                          </span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Expandable Unified Diff View */}
                {isExpanded && (
                  <div className="diff-content-panel">
                    {hasDiff ? (
                      <div className="diff-viewer">
                        {f.diffContent!.split('\n').map((line, idx) => renderDiffLine(line, idx))}
                      </div>
                    ) : (
                      <div className="no-diff-notice">
                        <span>Binary file or no unified hunk text available.</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </section>
  );
};
