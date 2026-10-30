import { useEffect, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity,
  Check,
  Compass,
  GitBranch,
  Github,
  Home,
  LayoutDashboard,
  Moon,
  Plus,
  Search,
  Sun,
  Workflow,
  X,
} from 'lucide-react';
import { PageId } from '../../types';
import { useTheme } from '../../context/ThemeContext';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectPage: (page: PageId) => void;
  onConnectRepo: () => void;
  onHome: () => void;
}

interface CommandItem {
  id: string;
  title: string;
  category: 'Navigation' | 'Actions' | 'Appearance';
  icon: typeof LayoutDashboard;
  run: () => void;
}

export function CommandPalette({
  isOpen,
  onClose,
  onSelectPage,
  onConnectRepo,
  onHome,
}: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const { theme, toggleTheme } = useTheme();

  const commands: CommandItem[] = useMemo(
    () => [
      {
        id: 'nav-overview',
        title: 'Go to Overview',
        category: 'Navigation',
        icon: LayoutDashboard,
        run: () => {
          onSelectPage('overview');
          onClose();
        },
      },
      {
        id: 'nav-repos',
        title: 'Go to Repositories',
        category: 'Navigation',
        icon: Github,
        run: () => {
          onSelectPage('repositories');
          onClose();
        },
      },
      {
        id: 'nav-analysis',
        title: 'Go to Change Analysis',
        category: 'Navigation',
        icon: GitBranch,
        run: () => {
          onSelectPage('analysis');
          onClose();
        },
      },
      {
        id: 'nav-dependencies',
        title: 'Go to Dependency Map',
        category: 'Navigation',
        icon: Workflow,
        run: () => {
          onSelectPage('dependencies');
          onClose();
        },
      },
      {
        id: 'nav-tests',
        title: 'Go to Test Intelligence',
        category: 'Navigation',
        icon: Check,
        run: () => {
          onSelectPage('tests');
          onClose();
        },
      },
      {
        id: 'nav-reports',
        title: 'Go to Risk Reports',
        category: 'Navigation',
        icon: Activity,
        run: () => {
          onSelectPage('reports');
          onClose();
        },
      },
      {
        id: 'act-connect',
        title: 'Connect GitHub Repository',
        category: 'Actions',
        icon: Plus,
        run: () => {
          onClose();
          onConnectRepo();
        },
      },
      {
        id: 'act-landing',
        title: 'Exit to Landing Page',
        category: 'Actions',
        icon: Home,
        run: () => {
          onClose();
          onHome();
        },
      },
      {
        id: 'act-theme',
        title: theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme',
        category: 'Appearance',
        icon: theme === 'dark' ? Sun : Moon,
        run: () => {
          toggleTheme();
          onClose();
        },
      },
    ],
    [onSelectPage, onClose, onConnectRepo, onHome, theme, toggleTheme]
  );

  const filtered = useMemo(() => {
    if (!query.trim()) return commands;
    const q = query.toLowerCase();
    return commands.filter(
      (c) => c.title.toLowerCase().includes(q) || c.category.toLowerCase().includes(q)
    );
  }, [commands, query]);

  // Reset selected index when query changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Keyboard navigation & ESC handler
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % (filtered.length || 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + (filtered.length || 1)) % (filtered.length || 1));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filtered[selectedIndex]) {
          filtered[selectedIndex].run();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, filtered, selectedIndex]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="modal-backdrop command-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          onClick={(e) => {
            if (e.target === e.currentTarget) onClose();
          }}
          role="dialog"
          aria-modal="true"
        >
          <motion.div
            className="command-modal"
            initial={{ opacity: 0, scale: 0.97, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: -10 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
          >
            <div className="command-search-bar">
              <Search size={16} className="command-search-icon" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Type a command or search workspace..."
                autoFocus
              />
              <button
                className="icon-button command-close-btn"
                onClick={onClose}
                type="button"
                aria-label="Close"
              >
                <X size={16} />
              </button>
            </div>

            <div className="command-list" role="listbox">
              {filtered.length === 0 ? (
                <div className="command-empty">No matching commands found.</div>
              ) : (
                filtered.map((cmd, idx) => {
                  const Icon = cmd.icon;
                  const isSelected = idx === selectedIndex;
                  return (
                    <button
                      key={cmd.id}
                      className={`command-item ${isSelected ? 'active' : ''}`}
                      onClick={() => cmd.run()}
                      onMouseEnter={() => setSelectedIndex(idx)}
                      role="option"
                      aria-selected={isSelected}
                      type="button"
                    >
                      <span className="command-icon">
                        <Icon size={16} />
                      </span>
                      <span className="command-title">{cmd.title}</span>
                      <span className="command-category">{cmd.category}</span>
                    </button>
                  );
                })
              )}
            </div>

            <div className="command-footer">
              <span>Use <kbd>↑</kbd> <kbd>↓</kbd> to navigate</span>
              <span><kbd>Enter</kbd> to select</span>
              <span><kbd>Esc</kbd> to close</span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
