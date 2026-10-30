import { ArrowUpRight, Moon, Sun } from 'lucide-react';
import { Brand } from '../ui/Brand';
import { User } from '../../types';
import { useTheme } from '../../context/ThemeContext';

interface LandingNavProps {
  currentUser?: User | null;
  onLaunch: () => void;
  onSignIn: () => void;
  onHome?: () => void;
}

export function LandingNav({ currentUser, onLaunch, onSignIn, onHome }: LandingNavProps) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <header className="marketing-header">
      <nav className="marketing-nav wrap">
        <a href="#landing" className="brand-link" onClick={(e) => { e.preventDefault(); onHome?.(); }} title="ChangeRadar — Return to homepage">
          <Brand size="md" light={isDark} />
        </a>
        <div className="marketing-links">
          <a href="#product">Product</a>
          <a href="#how">How it works</a>
          <a href="#principles">Principles</a>
          <a href="https://changeradar-api.onrender.com/docs" target="_blank" rel="noreferrer">API Docs</a>
        </div>
        <div className="marketing-actions">
          <button className="theme-toggle" onClick={toggleTheme} type="button" aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`} title={`Switch to ${isDark ? 'light' : 'dark'} mode`}>
            {isDark ? <Sun size={16} /> : <Moon size={16} />}
            <span>{isDark ? 'Light mode' : 'Dark mode'}</span>
          </button>
          {currentUser ? (
            <>
              <div className="marketing-user"><span className="marketing-avatar">{currentUser.name ? currentUser.name.slice(0, 2).toUpperCase() : 'CR'}</span><span>{currentUser.name}</span></div>
              <button className="button button-lime button-nav" onClick={onLaunch} type="button"><span>Go to workspace</span><ArrowUpRight size={15} /></button>
            </>
          ) : (
            <>
              <button className="nav-signin-btn" onClick={onSignIn} type="button">Sign in</button>
              <button className="button button-dark button-nav" onClick={onLaunch} type="button"><span>Open workspace</span><ArrowUpRight size={15} /></button>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
