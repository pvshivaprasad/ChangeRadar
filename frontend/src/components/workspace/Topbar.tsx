import { useState } from 'react';
import { ArrowUpRight, Bell, LogOut, Menu, Search, User as UserIcon } from 'lucide-react';
import { StatusBadge } from '../ui/StatusBadge';
import { ThemeToggle } from '../ui/ThemeToggle';
import { User } from '../../types';

interface TopbarProps {
  pageLabel: string;
  onOpenSidebar: () => void;
  onOpenCommandPalette: () => void;
  onAuth?: () => void;
  onLogout?: () => void;
  currentUser?: User | null;
}

export function Topbar({
  pageLabel,
  onOpenSidebar,
  onOpenCommandPalette,
  onAuth,
  onLogout,
  currentUser,
}: TopbarProps) {
  const [showMenu, setShowMenu] = useState(false);
  const isMac = typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform);

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button
          className="icon-button mobile-menu"
          onClick={onOpenSidebar}
          aria-label="Open menu"
          type="button"
        >
          <Menu size={20} />
        </button>
        <div className="breadcrumbs">
          <span className="breadcrumb-muted">Workspace</span>
          <span className="breadcrumb-slash">/</span>
          <span className="breadcrumb-current">{pageLabel}</span>
        </div>
      </div>

      <div className="topbar-right">
        <button
          className="search-shortcut"
          onClick={onOpenCommandPalette}
          title="Search workspace (Ctrl+K or ⌘K)"
          type="button"
        >
          <Search size={15} />
          <span>Quick actions & search</span>
          <kbd>{isMac ? '⌘ K' : 'Ctrl K'}</kbd>
        </button>

        <StatusBadge />

        <ThemeToggle />

        <button
          className="icon-button"
          title="Workspace Notifications"
          aria-label="Notifications"
          type="button"
        >
          <Bell size={18} />
        </button>

        <div style={{ position: 'relative' }}>
          <button
            className="top-avatar-btn"
            onClick={() => setShowMenu(!showMenu)}
            title={
              currentUser
                ? `Account: ${currentUser.name} (${currentUser.email})`
                : 'Account & Authentication'
            }
            type="button"
          >
            <span className="top-avatar">
              {currentUser?.name ? currentUser.name.slice(0, 2).toUpperCase() : 'CR'}
            </span>
          </button>

          {showMenu && (
            <div
              className="surface-card topbar-account-menu"
              style={{
                position: 'absolute',
                top: 'calc(100% + 8px)',
                right: 0,
                width: '240px',
                background: 'var(--ws-surface)',
                border: '1px solid var(--ws-border)',
                borderRadius: '12px',
                padding: '14px',
                boxShadow: '0 12px 32px rgba(0, 0, 0, 0.45)',
                zIndex: 150,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  marginBottom: '10px',
                  paddingBottom: '10px',
                  borderBottom: '1px solid var(--ws-border)',
                }}
              >
                <span className="top-avatar" style={{ width: '32px', height: '32px', fontSize: '12px' }}>
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

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <a
                  href="http://localhost:8000/docs"
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '12px',
                    color: 'var(--ws-text-muted)',
                    textDecoration: 'none',
                    padding: '6px 8px',
                    borderRadius: '6px',
                  }}
                  onClick={() => setShowMenu(false)}
                >
                  <span>API Documentation</span>
                  <ArrowUpRight size={13} />
                </a>

                {onLogout && (
                  <button
                    className="button button-dark"
                    onClick={() => {
                      setShowMenu(false);
                      onLogout();
                    }}
                    style={{
                      width: '100%',
                      padding: '8px 10px',
                      fontSize: '12px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px',
                      color: '#d66e68',
                      borderColor: 'rgba(214, 110, 104, 0.3)',
                      marginTop: '4px',
                    }}
                    type="button"
                  >
                    <LogOut size={13} />
                    <span>Sign out</span>
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
