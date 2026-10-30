import { ArrowUpRight } from 'lucide-react';
import { Brand } from '../ui/Brand';

export function LandingNav({ onLaunch }: { onLaunch: () => void }) {
  return (
    <nav className="marketing-nav wrap">
      <Brand />
      <div className="marketing-links">
        <a href="#product">Product</a>
        <a href="#how">How it works</a>
        <a href="#principles">Principles</a>
      </div>
      <button
        className="button button-dark button-small"
        onClick={onLaunch}
        type="button"
      >
        Open workspace <ArrowUpRight size={14} />
      </button>
    </nav>
  );
}
