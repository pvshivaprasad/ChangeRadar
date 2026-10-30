import { ArrowUpRight } from 'lucide-react';
import { Brand } from '../ui/Brand';

interface LandingNavProps {
  onLaunch: () => void;
  onSignIn: () => void;
  onHome?: () => void;
}

export function LandingNav({ onLaunch, onSignIn, onHome }: LandingNavProps) {
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
        </div>
      </nav>
    </header>
  );
}
