import { ArrowRight, Code2, FolderGit2, GitBranch, Github, Play, Plus, RefreshCw, ShieldCheck, Trash2 } from 'lucide-react';
import { EmptyState } from '../../ui/EmptyState';
import { RepositoryRecord } from '../../../types';

interface RepositoriesViewProps {
  repositories: RepositoryRecord[];
  onConnect: () => void;
  onAnalyzeRepo: (repo: RepositoryRecord) => void;
  onDeleteRepo: (id: number) => void;
  isLoading?: boolean;
}

export function RepositoriesView({
  repositories,
  onConnect,
  onAnalyzeRepo,
  onDeleteRepo,
  isLoading = false,
}: RepositoriesViewProps) {
  const hasRepos = repositories.length > 0;

  return (
    <div className="view-container">
      <section className="surface-card full-card">
        <div className="card-heading">
          <div>
            <h3>Connected Codebases</h3>
            <p>Repositories monitored for AST change detection, dependency mapping, and change impact</p>
          </div>
          <button
            className="button button-lime button-small"
            onClick={onConnect}
            type="button"
          >
            <Plus size={16} /> Import local repository
          </button>
        </div>

        {hasRepos ? (
          <div className="repo-cards-grid" style={{ display: 'grid', gap: '16px', margin: '20px 0' }}>
            {repositories.map((repo) => (
              <div
                key={repo.id}
                className="surface-card"
                style={{
                  border: '1px solid var(--ws-border)',
                  borderRadius: '12px',
                  padding: '20px 24px',
                  background: 'var(--ws-surface-subtle)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '16px',
                }}
              >
                <div style={{ flex: '1 1 340px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                    <FolderGit2 size={20} color="var(--lime)" />
                    <b style={{ fontSize: '17px', color: 'var(--ws-text)' }}>{repo.name}</b>
                    <span
                      style={{
                        fontSize: '11px',
                        fontFamily: 'var(--font-mono)',
                        background: 'rgba(199, 243, 107, 0.12)',
                        color: 'var(--lime)',
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontWeight: 600,
                      }}
                    >
                      {repo.default_branch}
                    </span>
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--ws-text-muted)', marginBottom: '10px', wordBreak: 'break-all' }}>
                    {repo.path}
                  </div>
                  <div style={{ display: 'flex', gap: '18px', fontSize: '13px', color: 'var(--ws-text-faint)' }}>
                    <span><b>{repo.file_count}</b> Python files</span>
                    <span>•</span>
                    <span><b>{repo.symbol_count}</b> AST symbols</span>
                    <span>•</span>
                    <span><b>{repo.edge_count}</b> Call edges</span>
                    {repo.last_scanned_at && (
                      <>
                        <span>•</span>
                        <span>Scanned {new Date(repo.last_scanned_at).toLocaleTimeString()}</span>
                      </>
                    )}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <button
                    className="button button-lime button-small"
                    onClick={() => onAnalyzeRepo(repo)}
                    type="button"
                    title="Launch change impact analysis on this repository"
                  >
                    <Play size={14} /> Analyze Changes
                  </button>
                  <button
                    className="icon-button"
                    onClick={() => {
                      if (
                        window.confirm(
                          `Are you sure you want to remove '${repo.name}' from your workspace?\n\nAll historical change impact reports will be safely preserved in your audit records.`
                        )
                      ) {
                        onDeleteRepo(repo.id);
                      }
                    }}
                    type="button"
                    style={{ color: '#d66e68' }}
                    title="Remove repository from workspace"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No repositories imported yet"
            description="Import a local Python repository to scan its file structure, parse AST symbol hierarchies, and calculate blast radius across commits."
            action="Import local repository"
            onAction={onConnect}
            icon={<FolderGit2 size={28} />}
          />
        )}

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
