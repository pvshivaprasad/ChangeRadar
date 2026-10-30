import { Bell, Menu, Search } from 'lucide-react';
import { StatusBadge } from '../ui/StatusBadge';
import { ThemeToggle } from '../ui/ThemeToggle';
import { PageId } from '../../types';

interface TopbarProps {
  pageLabel: string;
  onOpenSidebar: () => void;
  onOpenCommandPalette: () => void;
}

export function Topbar({
  pageLabel,
  onOpenSidebar,
  onOpenCommandPalette,
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
          <Menu size={18} />
        </button>
        <span className="breadcrumb-muted">Workspace</span>
        <span className="breadcrumb-slash">/</span>
        <span className="breadcrumb-current">{pageLabel}</span>
      </div>

      <div className="topbar-right">
        <button
          className="search-shortcut"
          onClick={onOpenCommandPalette}
          title="Search workspace (Ctrl+K or ⌘K)"
          type="button"
        >
          <Search size={14} />
          <span>Search</span>
          <kbd>{isMac ? '⌘ K' : 'Ctrl K'}</kbd>
        </button>

        <StatusBadge />

        <ThemeToggle />

        <button
          className="icon-button"
          title="Notifications"
          aria-label="Notifications"
          type="button"
        >
          <Bell size={16} />
        </button>

        <span className="top-avatar" title="Signed in as Lead Engineer">
          CR
        </span>
      </div>
    </header>
  );
}
