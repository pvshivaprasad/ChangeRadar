import {
  Activity,
  ArrowUpRight,
  Check,
  ChevronDown,
  CircleHelp,
  GitBranch,
  Github,
  LayoutDashboard,
  LogOut,
  Settings2,
  Workflow,
  X,
} from 'lucide-react';
import { Brand } from '../ui/Brand';
import { NavItem, PageId } from '../../types';

export const navItems: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'repositories', label: 'Repositories', icon: Github },
  { id: 'analysis', label: 'Change analysis', icon: GitBranch, badge: 'NEW' },
  { id: 'dependencies', label: 'Dependency map', icon: Workflow },
  { id: 'tests', label: 'Test intelligence', icon: Check },
  { id: 'reports', label: 'Risk reports', icon: Activity },
];

interface SidebarProps {
  page: PageId;
  onSelectPage: (id: PageId) => void;
  isOpen: boolean;
  onClose: () => void;
  onHome: () => void;
  onAuth: () => void;
}

export function Sidebar({
  page,
  onSelectPage,
  isOpen,
  onClose,
  onHome,
  onAuth,
}: SidebarProps) {
  return (
    <>
      {isOpen && (
        <button
          className="mobile-scrim"
          onClick={onClose}
          aria-label="Close navigation"
          type="button"
        />
      )}
      <aside className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-head">
          <button
            className="brand-button"
            onClick={onHome}
            title="Return to ChangeRadar homepage"
            type="button"
          >
            <Brand size="md" />
          </button>
          <button
            className="icon-button mobile-close"
            onClick={onClose}
            aria-label="Close navigation"
            type="button"
          >
            <X size={18} />
          </button>
        </div>

        <button className="workspace-switch" type="button">
          <span className="workspace-avatar">CR</span>
          <span className="workspace-switch-text">
            <b>Production Workspace</b>
            <small>Enterprise preview</small>
          </span>
          <ChevronDown size={15} />
        </button>

        <div className="nav-label">WORKSPACE VIEWS</div>
        <nav className="side-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = page === item.id;
            return (
              <button
                key={item.id}
                className={`nav-item ${isActive ? 'active' : ''}`}
                onClick={() => {
                  onSelectPage(item.id);
                  onClose();
                }}
                type="button"
              >
                <Icon size={18} />
                <span className="nav-item-label">{item.label}</span>
                {item.badge && <span className="nav-new">{item.badge}</span>}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-bottom">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="sidebar-help-link"
          >
            <div className="help-icon">
              <CircleHelp size={17} />
            </div>
            <div className="help-text">
              <b>API Reference</b>
              <small>Explore FastAPI Swagger docs</small>
            </div>
            <ArrowUpRight size={14} />
          </a>

          <div className="sidebar-user-card">
            <button className="profile-button" type="button" onClick={onAuth}>
              <span className="profile-avatar">CR</span>
              <span className="profile-info">
                <b>Lead Engineer</b>
                <small>Shiva Prasad · Workspace Admin</small>
              </span>
              <Settings2 size={16} />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
