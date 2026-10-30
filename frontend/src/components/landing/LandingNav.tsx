import { ArrowUpRight } from 'lucide-react';
import { Brand } from '../ui/Brand';
import { User } from '../../types';

interface LandingNavProps {
  currentUser?: User | null;
  onLaunch: () => void;
  onSignIn: () => void;
  onHome?: () => void;
}

export function LandingNav({ currentUser, onLaunch, onSignIn, onHome }: LandingNavProps) {
  return (
    <header className="marketing-header">
      <nav className="marketing-nav wrap">
        <a
          href="#landing"
          className="brand-link"
          onClick={(e) => {
            e.preventDefault();
            onHome?.();
          }}
          title="ChangeRadar — Return to homepage"
        >
          <Brand size="md" light />
        </a>

        <div className="marketing-links">
          <a href="#product">Product</a>
          <a href="#how">How it works</a>
          <a href="#principles">Principles</a>
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
            API Docs
          </a>
        </div>

        <div className="marketing-actions">
          {currentUser ? (
            <>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '13px',
                  color: 'var(--ws-text-muted)',
                  paddingRight: '6px',
                }}
              >
                <span
                  style={{
                    width: '26px',
                    height: '26px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--lime)',
                    color: '#171916',
                    display: 'grid',
                    placeItems: 'center',
                    fontWeight: 700,
                    fontSize: '11px',
                  }}
                >
                  {currentUser.name ? currentUser.name.slice(0, 2).toUpperCase() : 'CR'}
                </span>
                <span style={{ fontWeight: 600, color: 'var(--ws-text)' }}>
                  {currentUser.name}
                </span>
              </div>
              <button
                className="button button-lime button-nav"
                onClick={onLaunch}
                type="button"
              >
                <span>Go to workspace</span>
                <ArrowUpRight size={15} />
              </button>
            </>
          ) : (
            <>
              <button className="nav-signin-btn" onClick={onSignIn} type="button">
                Sign in
              </button>
              <button
                className="button button-dark button-nav"
                onClick={onLaunch}
                type="button"
              >
                <span>Open workspace</span>
                <ArrowUpRight size={15} />
              </button>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
