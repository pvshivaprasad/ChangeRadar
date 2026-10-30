import { useEffect, useState } from 'react';
import { Plus } from 'lucide-react';
import {
  AnalysisRecord,
  ImpactAnalysisReport,
  PageId,
  RepositoryRecord,
  ScanSummary,
  User,
} from '../../types';
import {
  analyzeRepository,
  deleteRepository,
  fetchAllAnalyses,
  fetchRepositories,
  fetchSampleAnalysis,
  fetchSampleScan,
  getActiveAnalysisId,
  scanRepository,
  setActiveAnalysisId,
} from '../../api/client';
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
  onLogout?: () => void;
  currentUser?: User | null;
}

export function Workspace({ onHome, onLogout, currentUser }: WorkspaceProps) {
  const [page, setPageState] = useState<PageId>(() => {
    try {
      const saved = localStorage.getItem('changeradar_ws_page');
      if (
        saved &&
        ['overview', 'repositories', 'analysis', 'dependencies', 'tests', 'reports'].includes(saved)
      ) {
        return saved as PageId;
      }
    } catch {
      // Ignore storage restrictions
    }
    return 'overview';
  });

  const setPage = (newPage: PageId) => {
    setPageState(newPage);
    try {
      localStorage.setItem('changeradar_ws_page', newPage);
    } catch {
      // Ignore
    }
  };

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showConnect, setShowConnect] = useState(false);
  const [showCommandPalette, setShowCommandPalette] = useState(false);

  // Real Repository Intelligence States
  const [repositories, setRepositories] = useState<RepositoryRecord[]>([]);
  const [analyses, setAnalyses] = useState<AnalysisRecord[]>([]);
  const [report, setReport] = useState<ImpactAnalysisReport | null>(null);
  const [scan, setScan] = useState<ScanSummary | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Automatically fetch initial sample scan & persisted repositories on first workspace entry
  useEffect(() => {
    let mounted = true;
    fetchRepositories()
      .then((repos) => {
        if (mounted) setRepositories(repos);
      })
      .catch(() => {});

    fetchAllAnalyses()
      .then((records) => {
        if (mounted) {
          setAnalyses(records);
          // Restore user's previous active analysis or latest completed analysis
          const activeId = getActiveAnalysisId();
          let target = records.find((r) => r.id === activeId);
          if (!target || !target.report) {
            target = records.find((r) => r.status === 'completed' && r.report) || records[0];
          }
          if (target && target.report) {
            setReport(target.report);
            setActiveAnalysisId(target.id);
          }
        }
      })
      .catch(() => {});

    fetchSampleScan()
      .then((data) => {
        if (mounted) setScan(data);
      })
      .catch(() => {});

    return () => {
      mounted = false;
    };
  }, []);

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

  const handleImportSuccess = (newRepo: RepositoryRecord) => {
    setRepositories((prev) => [newRepo, ...prev.filter((r) => r.id !== newRepo.id)]);
    fetchSampleScan().then(setScan).catch(() => {});
  };

  const handleDeleteRepo = async (id: number) => {
    try {
      await deleteRepository(id);
      setRepositories((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      console.error('Failed to delete repository', err);
    }
  };

  const handleAnalyzeRepo = async (repo: RepositoryRecord) => {
    setPage('analysis');
    handleCustomAnalysis(repo.path, 'HEAD~1', 'HEAD');
  };

  const handleRunSampleAnalysis = async () => {
    setIsAnalyzing(true);
    setAnalysisError(null);
    try {
      const data = await fetchSampleAnalysis();
      setReport(data);
      if (!scan) {
        const scanData = await fetchSampleScan();
        setScan(scanData);
      }
      const records = await fetchAllAnalyses();
      setAnalyses(records);
      if (records.length > 0 && records[0].id) {
        setActiveAnalysisId(records[0].id);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Analysis failed';
      setAnalysisError(msg);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCustomAnalysis = async (
    customPath: string,
    base: string,
    head: string
  ) => {
    setIsAnalyzing(true);
    setAnalysisError(null);
    try {
      const data = await analyzeRepository(customPath, base, head);
      setReport(data);
      const scanData = await scanRepository(customPath);
      setScan(scanData);
      const records = await fetchAllAnalyses();
      setAnalyses(records);
      if (records.length > 0 && records[0].id) {
        setActiveAnalysisId(records[0].id);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Custom analysis failed';
      setAnalysisError(msg);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSelectAnalysis = (record: AnalysisRecord) => {
    if (record.report) {
      setReport(record.report);
      setActiveAnalysisId(record.id);
      setPage('analysis');
    }
  };

  const handleScanSample = async () => {
    setIsAnalyzing(true);
    setAnalysisError(null);
    try {
      const scanData = await fetchSampleScan();
      setScan(scanData);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Scan failed';
      setAnalysisError(msg);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const activeItem = navItems.find((item) => item.id === page) ?? navItems[0];

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
        onLogout={onLogout}
        currentUser={currentUser}
      />

      <main className="workspace-main">
        <Topbar
          pageLabel={activeItem.label}
          onOpenSidebar={() => setSidebarOpen(true)}
          onOpenCommandPalette={() => setShowCommandPalette(true)}
          onLogout={onLogout}
          currentUser={currentUser}
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
            {page === 'analysis' && (
              <button
                className="button button-lime button-heading"
                onClick={handleRunSampleAnalysis}
                disabled={isAnalyzing}
                type="button"
              >
                <span>{isAnalyzing ? 'Analyzing...' : 'Run Sample Analysis'}</span>
              </button>
            )}
          </div>

          {page === 'overview' && (
            <OverviewView
              report={report}
              repositoriesCount={repositories.length}
              analysesCount={analyses.length}
              onConnectRepo={() => setShowConnect(true)}
              onNavigate={setPage}
              onRunSample={handleRunSampleAnalysis}
              isAnalyzing={isAnalyzing}
            />
          )}

          {page === 'repositories' && (
            <RepositoriesView
              repositories={repositories}
              onConnect={() => setShowConnect(true)}
              onAnalyzeRepo={handleAnalyzeRepo}
              onDeleteRepo={handleDeleteRepo}
              isLoading={isAnalyzing}
            />
          )}

          {page === 'analysis' && (
            <AnalysisView
              report={report}
              analyses={analyses}
              onSelectAnalysis={handleSelectAnalysis}
              onNavigate={() => setPage('repositories')}
              onRunSample={handleRunSampleAnalysis}
              onCustomAnalyze={handleCustomAnalysis}
              isAnalyzing={isAnalyzing}
              error={analysisError}
            />
          )}

          {page === 'dependencies' && (
            <DependenciesView
              scan={scan}
              onScanSample={handleScanSample}
              isLoading={isAnalyzing}
            />
          )}

          {page === 'tests' && (
            <TestsView
              report={report}
              onRunSample={handleRunSampleAnalysis}
              isLoading={isAnalyzing}
            />
          )}

          {page === 'reports' && (
            <ReportsView
              report={report}
              analyses={analyses}
              onSelectAnalysis={handleSelectAnalysis}
              onRunSample={handleRunSampleAnalysis}
              isLoading={isAnalyzing}
            />
          )}
        </div>

        <footer className="workspace-footer">
          <div className="workspace-footer-left">
            <span>
              CHANGE RADAR <b>FOUNDATION v0.1.1</b>
            </span>
            <span className="footer-dot-sep">&bull;</span>
            <span>
              {report ? `EVALUATED SHA ${report.head_commit.slice(0, 7)}` : 'PROD RUNTIME READY'}
            </span>
          </div>
          <StatusBadge minimal={false} />
        </footer>
      </main>

      <ConnectRepoModal
        isOpen={showConnect}
        onClose={() => setShowConnect(false)}
        onImportSuccess={handleImportSuccess}
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
