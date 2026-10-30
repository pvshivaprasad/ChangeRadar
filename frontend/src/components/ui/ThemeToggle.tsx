import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      className="icon-button theme-toggle-btn"
      onClick={toggleTheme}
      title={theme === 'dark' ? 'Switch to Ivory (Light)' : 'Switch to Obsidian (Dark)'}
      aria-label="Toggle theme"
      type="button"
    >
      {theme === 'dark' ? (
        <Sun size={16} strokeWidth={1.8} className="theme-icon sun" />
      ) : (
        <Moon size={16} strokeWidth={1.8} className="theme-icon moon" />
      )}
    </button>
  );
}
