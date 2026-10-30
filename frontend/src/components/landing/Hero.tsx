import { useState } from 'react';
import {
  ArrowDownRight,
  ArrowRight,
  Boxes,
  Braces,
  GitBranch,
  LockKeyhole,
  Sparkles,
  Workflow,
  Zap,
} from 'lucide-react';

interface HeroProps {
  onLaunch: () => void;
}

export function Hero({ onLaunch }: HeroProps) {
  const [activeNode, setActiveNode] = useState<string | null>(null);

  const nodes = [
    { id: 'checkout', label: 'checkout.service', icon: Boxes, cls: 'node-a', impact: 'Direct dependent', tests: '3 tests' },
    { id: 'sessions', label: 'user.sessions', icon: LockKeyhole, cls: 'node-b', impact: 'Direct dependent', tests: '5 tests' },
    { id: 'payments', label: 'billing.gateway', icon: Zap, cls: 'node-c', impact: '2 hops downstream', tests: '4 tests' },
    { id: 'profile', label: 'identity.profile', icon: GitBranch, cls: 'node-d', impact: 'Downstream consumer', tests: '2 tests' },
  ];

  return (
    <section className="hero wrap">
      <div className="hero-copy">
        <div className="eyebrow">
          <span className="eyebrow-dot" />
          <span>SOFTWARE CHANGE IMPACT INTELLIGENCE</span>
        </div>

        <h1>
          See the impact
          <br />
          before it <em>happens.</em>
        </h1>

        <p className="hero-lede">
          Every pull request causes ripple effects across your codebase. ChangeRadar
          statically traces function and class dependency paths, isolates breaking risks,
          and flags exact tests to run before you merge.
        </p>

        <div className="hero-actions">
          <button
            className="button button-lime button-hero"
            onClick={onLaunch}
            type="button"
          >
            <span>Explore workspace preview</span>
            <ArrowRight size={18} />
          </button>
          <a className="text-link hero-secondary-link" href="#how">
            <span>How the analysis works</span>
            <ArrowDownRight size={17} />
          </a>
        </div>

        <div className="hero-proof">
          <div className="avatar-stack">
            <span>JD</span>
            <span>MK</span>
            <span>AS</span>
            <span>RL</span>
          </div>
          <div className="proof-text">
            <b>Built for thoughtful engineering teams.</b>
            <span>Statically verified • Deterministic commit SHAs • Zero code execution</span>
          </div>
        </div>
      </div>

      <div
        className="hero-art-container"
        aria-label="Interactive code dependency visualization"
      >
        <div className="hero-art">
          <div className="art-topline">
            <span className="art-tag">
              <Workflow size={13} />
              <span>DEPENDENCY GRAPH / 001</span>
            </span>
            <span className="live-indicator">
              <i />
              <span>STATIC CALL ENGINE READY</span>
            </span>
          </div>

          <div className="graph-canvas">
            <svg
              className="graph-lines"
              viewBox="0 0 620 440"
              preserveAspectRatio="xMidYMid meet"
              aria-hidden="true"
            >
              {/* Secondary dashed connection lines */}
              <path
                d="M310 220 L130 95 L50 220 M310 220 L490 90 L570 215 M310 220 L140 345 L50 280 M310 220 L480 345 L570 280 M130 95 L490 90 M140 345 L480 345"
                className="graph-line-bg"
              />
              {/* Highlighted active impact path */}
              <path
                className="graph-line-accent"
                d="M310 220 L490 90 L570 215 M310 220 L140 345"
              />
              {/* Radial orbits */}
              <circle cx="310" cy="220" r="95" className="orbit orbit-one" />
              <circle cx="310" cy="220" r="150" className="orbit orbit-two" />
            </svg>

            {/* Core Changed Symbol */}
            <div
              className={`graph-node node-core ${activeNode === 'core' ? 'node-hovered' : ''}`}
              onMouseEnter={() => setActiveNode('core')}
              onMouseLeave={() => setActiveNode(null)}
            >
              <span className="node-icon">
                <Braces size={22} />
              </span>
              <div className="node-info">
                <b>auth.service</b>
                <small>MODIFIED SYMBOL</small>
              </div>
            </div>

            {/* Satellite Nodes */}
            {nodes.map((n) => {
              const Icon = n.icon;
              const isHovered = activeNode === n.id;
              return (
                <div
                  key={n.id}
                  className={`graph-node ${n.cls} ${isHovered ? 'node-hovered' : ''}`}
                  onMouseEnter={() => setActiveNode(n.id)}
                  onMouseLeave={() => setActiveNode(null)}
                >
                  <span className="node-icon">
                    <Icon size={16} />
                  </span>
                  <div className="node-info">
                    <b>{n.label}</b>
                    <small>{n.impact}</small>
                  </div>
                </div>
              );
            })}

            {/* Graph Floating Status Pill */}
            <div className="graph-tag">
              <Sparkles size={13} />
              <span>4 downstream modules affected · 14 tests recommended</span>
            </div>
          </div>

          <div className="art-footer">
            <span>EVIDENCE TRACEABILITY</span>
            <span>AST symbol extraction & import provenance</span>
          </div>
        </div>
      </div>
    </section>
  );
}
