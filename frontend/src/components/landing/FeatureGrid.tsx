import { GitCommitHorizontal, ShieldCheck, Workflow } from 'lucide-react';

export function FeatureGrid() {
  return (
    <>
      <section className="ticker">
        <div className="wrap ticker-inner">
          <span>BUILT FOR COMPLEX CODEBASES</span>
          <span className="ticker-sep">/</span>
          <span>STATIC DEPENDENCY RESOLUTION</span>
          <span className="ticker-sep">/</span>
          <span>EVIDENCE-BASED CHANGE CONTEXT</span>
          <span className="ticker-sep">/</span>
          <span>DETERMINISTIC REGRESSION TESTING</span>
        </div>
      </section>

      <section className="feature-section wrap" id="product">
        <div className="section-intro">
          <div className="eyebrow">
            <span className="eyebrow-dot" />
            <span>A CLEARER VIEW OF CHANGE</span>
          </div>
          <h2>
            Less guesswork.
            <br />
            <em>Better engineering.</em>
          </h2>
          <p>
            ChangeRadar connects the dots between the code you touch and every
            subsystem that depends on it. Built on strict static analysis without
            untrusted runtime execution.
          </p>
        </div>

        <div className="feature-grid">
          <article className="feature-card feature-large">
            <div className="feature-card-content">
              <div className="feature-icon">
                <Workflow size={24} />
              </div>
              <span className="feature-index">01 / UNDERSTAND</span>
              <h3>Map every connection.</h3>
              <p>
                Explore how modules, functions, classes, and services connect across
                your codebase. Inspect static import trees and call provenance with
                file and line-number accuracy.
              </p>
            </div>
            <div className="mini-map" aria-hidden="true">
              <div className="mini-node mini-main">auth.service</div>
              <div className="mini-node mini-one">session.store</div>
              <div className="mini-node mini-two">checkout.flow</div>
              <div className="mini-node mini-three">user.profile</div>
              <svg viewBox="0 0 420 140" preserveAspectRatio="none">
                <path d="M210 70 L90 30 M210 70 L330 30 M210 70 L210 115" />
              </svg>
            </div>
          </article>

          <article className="feature-card">
            <div className="feature-card-content">
              <div className="feature-icon violet">
                <GitCommitHorizontal size={24} />
              </div>
              <span className="feature-index">02 / TRACE</span>
              <h3>Follow every change.</h3>
              <p>
                Compare Git revisions and inspect changed symbols. See whether a
                modification affects internal module implementation or impacts an
                exported public API contract.
              </p>
            </div>
            <div className="code-lines" aria-hidden="true">
              <div className="code-line-bar bar-1" />
              <div className="code-line-bar bar-2" />
              <div className="code-line-bar bar-3" />
              <div className="code-line-bar bar-4" />
              <div className="code-line-bar bar-5" />
            </div>
          </article>

          <article className="feature-card">
            <div className="feature-card-content">
              <div className="feature-icon amber">
                <ShieldCheck size={24} />
              </div>
              <span className="feature-index">03 / ASSESS</span>
              <h3>Surface what matters.</h3>
              <p>
                Prioritize change impact with transparent evidence. Identify exactly
                which downstream modules require validation, and run only the tests
                that actually touch altered code paths.
              </p>
            </div>
            <div className="risk-preview">
              <span className="risk-item">
                <i /> Dependency traversal path
              </span>
              <span className="risk-item">
                <i /> Targeted test recommendations
              </span>
              <span className="risk-item">
                <i /> Public API contract boundary
              </span>
            </div>
          </article>
        </div>
      </section>
    </>
  );
}
