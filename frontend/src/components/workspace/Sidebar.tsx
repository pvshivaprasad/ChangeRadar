import {
  Activity,
  ArrowUpRight,
  Check,
  ChevronDown,
  CircleHelp,
  GitBranch,
  Github,
  LayoutDashboard,
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
}

export function Sidebar({
  page,
  onSelectPage,
  isOpen,
  onClose,
  onHome,
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
            <Brand />
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
          <span>
            <b>Engineering Team</b>
            <small>Personal workspace</small>
          </span>
          <ChevronDown size={14} />
        </button>

        <div className="nav-label">WORKSPACE</div>
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
                <Icon size={16} />
                <span>{item.label}</span>
                {item.badge && <span className="nav-new">{item.badge}</span>}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-help">
            <div className="help-icon">
              <CircleHelp size={16} />
            </div>
            <div>
              <b>Need a hand?</b>
              <small>Explore architecture & docs</small>
            </div>
            <ArrowUpRight size={13} />
          </div>

          <button className="profile-button" type="button">
            <span className="profile-avatar">CR</span>
            <span>
              <b>Lead Engineer</b>
              <small>Workspace admin</small>
            </span>
            <Settings2 size={15} />
          </button>
        </div>
      </aside>
    </>
  );
}
