import {
  ArrowDownRight,
  ArrowRight,
  Boxes,
  Braces,
  GitBranch,
  LockKeyhole,
  Zap,
} from 'lucide-react';

export function Hero({ onLaunch }: { onLaunch: () => void }) {
  return (
    <section className="hero wrap">
      <div className="hero-copy">
        <div className="eyebrow">
          <span className="eyebrow-dot" /> SOFTWARE CHANGE INTELLIGENCE
        </div>
        <h1>
          See the impact
          <br />
          before it <em>happens.</em>
        </h1>
        <p className="hero-lede">
          Every code change has a ripple effect. Understand dependencies, surface
          potential risks, and give your team the context to ship with
          confidence.
        </p>
        <div className="hero-actions">
          <button
            className="button button-lime"
            onClick={onLaunch}
            type="button"
          >
            Explore the workspace <ArrowRight size={17} />
          </button>
          <a className="text-link" href="#how">
            See how it works <ArrowDownRight size={16} />
          </a>
        </div>
        <div className="hero-proof">
          <div className="avatar-stack">
            <span>JD</span>
            <span>MK</span>
            <span>AS</span>
          </div>
          <span>Built for the people behind the code.</span>
        </div>
      </div>

      <div
        className="hero-art"
        aria-label="Illustrative code dependency visualization"
      >
        <div className="art-topline">
          <span>CHANGE GRAPH / 001</span>
          <span className="live-indicator">
            <i /> LIVE SYSTEM VIEW
          </span>
        </div>
        <div className="graph-canvas">
          <svg
            className="graph-lines"
            viewBox="0 0 560 430"
            preserveAspectRatio="xMidYMid meet"
            aria-hidden="true"
          >
            <path d="M280 211 L140 112 L66 220 M280 211 L424 105 L496 225 M280 211 L151 337 L67 275 M280 211 L417 337 L500 280 M140 112 L424 105 M151 337 L417 337" />
            <path
              className="graph-line-accent"
              d="M280 211 L424 105 L496 225 M280 211 L151 337"
            />
            <circle cx="280" cy="211" r="74" className="orbit orbit-one" />
            <circle cx="280" cy="211" r="111" className="orbit orbit-two" />
          </svg>
          <div className="graph-node node-core">
            <span className="node-icon">
              <Braces size={20} />
            </span>
            <b>auth.service</b>
            <small>CORE MODULE</small>
          </div>
          <div className="graph-node node-a">
            <span className="node-icon">
              <Boxes size={16} />
            </span>
            <b>checkout</b>
          </div>
          <div className="graph-node node-b">
            <span className="node-icon">
              <LockKeyhole size={16} />
            </span>
            <b>sessions</b>
          </div>
          <div className="graph-node node-c">
            <span className="node-icon">
              <Zap size={16} />
            </span>
            <b>payments</b>
          </div>
          <div className="graph-node node-d">
            <span className="node-icon">
              <GitBranch size={16} />
            </span>
            <b>user.profile</b>
          </div>
          <div className="graph-tag">
            <span /> 4 connected modules
          </div>
        </div>
        <div className="art-footer">
          <span>DEPENDENCY PREVIEW</span>
          <span>Illustrative visualization</span>
        </div>
      </div>
    </section>
  );
}
