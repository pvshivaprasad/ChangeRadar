import { useEffect, useState } from 'react';
import { Plus } from 'lucide-react';
import { PageId } from '../../types';
import { Sidebar, navItems } from './Sidebar';
import { Topbar } from './Topbar';
import { OverviewView } from './views/OverviewView';
import { RepositoriesView } from './views/RepositoriesView';
import { AnalysisView } from './views/AnalysisView';
import { DependenciesView } from './views/DependenciesView';
import { TestsView } from './views/TestsView';
import { ReportsView } from './views/ReportsView';
import { ConnectRepoModal } from '../modals/ConnectRepoModal';
import { CommandPalette } from '../modals/CommandPalette';
import { StatusBadge } from '../ui/StatusBadge';

interface WorkspaceProps {
  onHome: () => void;
  onAuth: () => void;
}

export function Workspace({ onHome, onAuth }: WorkspaceProps) {
  const [page, setPage] = useState<PageId>('overview');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showConnect, setShowConnect] = useState(false);
  const [showCommandPalette, setShowCommandPalette] = useState(false);

  const activeItem = navItems.find((item) => item.id === page) ?? navItems[0];

  // Global Ctrl+K / Cmd+K listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setShowCommandPalette((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const pageHeadings: Record<PageId, { title: string; subtitle: string }> = {
    overview: {
      title: 'Engineering Overview',
      subtitle: 'Your change intelligence picture, call graphs, and blast radius context all in one place.',
    },
    repositories: {
      title: 'Connected Repositories',
      subtitle: 'Manage repositories monitored for AST symbol extraction and Git diff tracking.',
    },
    analysis: {
      title: 'Change Impact Analysis',
      subtitle: 'Compare Git revisions and evaluate potential downstream blast radius before merging.',
    },
    dependencies: {
      title: 'Dependency Explorer',
      subtitle: 'Interactive DAG representation of module, class, and function call hierarchies.',
    },
    tests: {
      title: 'Test Intelligence',
      subtitle: 'Targeted test suite recommendations based on modified code paths and coverage gaps.',
    },
    reports: {
      title: 'Risk & Audit Reports',
      subtitle: 'Traceable, reproducible change impact assessments tied to immutable commit SHAs.',
    },
  };

  const { title, subtitle } = pageHeadings[page];

  return (
    <div className="workspace-shell">
      <Sidebar
        page={page}
        onSelectPage={setPage}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onHome={onHome}
        onAuth={onAuth}
      />

      <main className="workspace-main">
        <Topbar
          pageLabel={activeItem.label}
          onOpenSidebar={() => setSidebarOpen(true)}
          onOpenCommandPalette={() => setShowCommandPalette(true)}
          onAuth={onAuth}
        />

        <div className="page-content">
          <div className="page-heading">
            <div className="heading-copy">
              <div className="eyebrow">
                <span className="eyebrow-dot" />
                <span>PERSONAL WORKSPACE &bull; ENTERPRISE PREVIEW</span>
              </div>
              <h1>{title}</h1>
              <p className="page-subtitle">{subtitle}</p>
            </div>
            {page === 'repositories' && (
              <button
                className="button button-lime button-heading"
                onClick={() => setShowConnect(true)}
                type="button"
              >
                <Plus size={16} />
                <span>Connect repository</span>
              </button>
            )}
          </div>

          {page === 'overview' && (
            <OverviewView
              onConnectRepo={() => setShowConnect(true)}
              onNavigate={setPage}
            />
          )}
          {page === 'repositories' && (
            <RepositoriesView onConnect={() => setShowConnect(true)} />
          )}
          {page === 'analysis' && (
            <AnalysisView onNavigate={() => setPage('repositories')} />
          )}
          {page === 'dependencies' && <DependenciesView />}
          {page === 'tests' && <TestsView />}
          {page === 'reports' && <ReportsView />}
        </div>

        <footer className="workspace-footer">
          <div className="workspace-footer-left">
            <span>
              CHANGE RADAR <b>FOUNDATION v0.1.1</b>
            </span>
            <span className="footer-dot-sep">&bull;</span>
            <span>PROD RUNTIME READY</span>
          </div>
          <StatusBadge minimal={false} />
        </footer>
      </main>

      <ConnectRepoModal
        isOpen={showConnect}
        onClose={() => setShowConnect(false)}
      />

      <CommandPalette
        isOpen={showCommandPalette}
        onClose={() => setShowCommandPalette(false)}
        onSelectPage={setPage}
        onConnectRepo={() => setShowConnect(true)}
        onHome={onHome}
      />
    </div>
  );
}
