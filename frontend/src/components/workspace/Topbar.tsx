import { Bell, Menu, Search, User } from 'lucide-react';
import { StatusBadge } from '../ui/StatusBadge';
import { ThemeToggle } from '../ui/ThemeToggle';

interface TopbarProps {
  pageLabel: string;
  onOpenSidebar: () => void;
  onOpenCommandPalette: () => void;
  onAuth: () => void;
}

export function Topbar({
  pageLabel,
  onOpenSidebar,
  onOpenCommandPalette,
  onAuth,
}: TopbarProps) {
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

        <button
          className="top-avatar-btn"
          onClick={onAuth}
          title="Account & Authentication"
          type="button"
        >
          <span className="top-avatar">CR</span>
        </button>
      </div>
    </header>
  );
}
