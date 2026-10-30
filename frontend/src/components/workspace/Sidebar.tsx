import { useState } from 'react';
import {
  Activity,
  ArrowUpRight,
  Check,
  ChevronDown,
  CircleHelp,
  GitBranch,
  Github,
  GitPullRequest,
  History,
  LayoutDashboard,
  LogOut,
  Settings2,
  Workflow,
  X,
} from 'lucide-react';
import { Brand } from '../ui/Brand';
import { NavItem, PageId, User } from '../../types';

export const navItems: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'repositories', label: 'Repositories', icon: Github },
  { id: 'pull-requests', label: 'Pull requests', icon: GitPullRequest, badge: 'v1.0' },
  { id: 'analysis', label: 'Change analysis', icon: GitBranch },
  { id: 'historical', label: 'Historical intelligence', icon: History, badge: 'HOT' },
  { id: 'dependencies', label: 'Dependency map', icon: Workflow },
  { id: 'tests', label: 'Test intelligence', icon: Check },
  { id: 'reports', label: 'Risk reports', icon: Activity },
  { id: 'settings', label: 'Integrations', icon: Settings2 },
];

interface SidebarProps {
  page: PageId;
  onSelectPage: (id: PageId) => void;
  isOpen: boolean;
  onClose: () => void;
  onHome: () => void;
  onAuth?: () => void;
  onLogout?: () => void;
  currentUser?: User | null;
}

export function Sidebar({
  page,
  onSelectPage,
  isOpen,
  onClose,
  onHome,
  onAuth,
  onLogout,
  currentUser,
}: SidebarProps) {
  const [showUserMenu, setShowUserMenu] = useState(false);

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

          <div className="sidebar-user-card" style={{ position: 'relative' }}>
            {showUserMenu && (
              <div
                className="surface-card user-popup-menu"
                style={{
                  position: 'absolute',
                  bottom: '100%',
                  left: 0,
                  right: 0,
                  marginBottom: '10px',
                  background: 'var(--ws-surface)',
                  border: '1px solid var(--ws-border)',
                  borderRadius: '12px',
                  padding: '14px',
                  boxShadow: '0 12px 32px rgba(0, 0, 0, 0.45)',
                  zIndex: 100,
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    marginBottom: '12px',
                    paddingBottom: '12px',
                    borderBottom: '1px solid var(--ws-border)',
                  }}
                >
                  <span className="profile-avatar">
                    {currentUser?.name ? currentUser.name.slice(0, 2).toUpperCase() : 'CR'}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <b
                      style={{
                        display: 'block',
                        fontSize: '13px',
                        color: 'var(--ws-text)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {currentUser?.name || 'Lead Engineer'}
                    </b>
                    <small
                      style={{
                        display: 'block',
                        fontSize: '11px',
                        color: 'var(--ws-text-muted)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {currentUser?.email || 'dev@changeradar.io'}
                    </small>
                  </div>
                </div>

                <div
                  style={{
                    fontSize: '11px',
                    color: 'var(--ws-text-faint)',
                    marginBottom: '12px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                  }}
                >
                  <span>
                    ROLE: <b>Workspace Administrator</b>
                  </span>
                  <span>
                    STATUS: <b style={{ color: 'var(--lime)' }}>Active Verified Session</b>
                  </span>
                </div>

                {onLogout && (
                  <button
                    className="button button-dark"
                    onClick={() => {
                      setShowUserMenu(false);
                      onLogout();
                    }}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      fontSize: '12px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px',
                      color: '#d66e68',
                      borderColor: 'rgba(214, 110, 104, 0.3)',
                    }}
                    type="button"
                  >
                    <LogOut size={14} />
                    <span>Sign out of ChangeRadar</span>
                  </button>
                )}
              </div>
            )}

            <button
              className="profile-button"
              onClick={() => setShowUserMenu(!showUserMenu)}
              style={{
                display: 'flex',
                alignItems: 'center',
                width: '100%',
                padding: '10px 12px',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                textAlign: 'left',
              }}
              type="button"
              title="Click to view account and logout options"
            >
              <span className="profile-avatar">
                {currentUser?.name ? currentUser.name.slice(0, 2).toUpperCase() : 'CR'}
              </span>
              <span className="profile-info" style={{ flex: 1, minWidth: 0 }}>
                <b
                  style={{
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    display: 'block',
                  }}
                >
                  {currentUser?.name || 'Lead Engineer'}
                </b>
                <small
                  style={{
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    display: 'block',
                  }}
                >
                  {currentUser?.email || 'dev@changeradar.io'}
                </small>
              </span>
              <Settings2 size={16} />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
