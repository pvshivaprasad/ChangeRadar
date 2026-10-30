import { GitCommitHorizontal, ShieldCheck, Workflow } from 'lucide-react';

export function FeatureGrid() {
  return (
    <>
      <section className="ticker">
        <div className="wrap ticker-inner">
          <span>BUILT FOR COMPLEX CODEBASES</span>
          <span>DEPENDENCY AWARE</span>
          <span>CHANGE CONTEXT</span>
          <span>ENGINEERING CONFIDENCE</span>
        </div>
      </section>

      <section className="feature-section wrap" id="product">
        <div className="section-intro">
          <div className="eyebrow">A CLEARER VIEW OF CHANGE</div>
          <h2>
            Less guesswork.
            <br />
            <em>Better engineering.</em>
          </h2>
          <p>
            ChangeRadar connects the dots between the code you touch and the
            systems that may depend on it.
          </p>
        </div>

        <div className="feature-grid">
          <article className="feature-card feature-large">
            <div className="feature-icon">
              <Workflow size={21} />
            </div>
            <div>
              <span className="feature-index">01 / UNDERSTAND</span>
              <h3>Map the connections.</h3>
              <p>
                Explore how modules, functions and services relate to one another
                in a codebase with static call provenance.
              </p>
            </div>
            <div className="mini-map" aria-hidden="true">
              <div className="mini-node mini-main">auth</div>
              <div className="mini-node mini-one">session</div>
              <div className="mini-node mini-two">checkout</div>
              <div className="mini-node mini-three">profile</div>
              <svg viewBox="0 0 360 120">
                <path d="M180 60 L70 25 M180 60 L290 25 M180 60 L180 105" />
              </svg>
            </div>
          </article>

          <article className="feature-card">
            <div className="feature-icon violet">
              <GitCommitHorizontal size={21} />
            </div>
            <span className="feature-index">02 / TRACE</span>
            <h3>Follow every change.</h3>
            <p>
              Compare revisions and see exactly which files, symbols, and
              dependencies are altered across commits.
            </p>
            <div className="code-lines" aria-hidden="true">
              <i />
              <i />
              <i />
              <i />
              <i />
            </div>
          </article>

          <article className="feature-card">
            <div className="feature-icon amber">
              <ShieldCheck size={21} />
            </div>
            <span className="feature-index">03 / ASSESS</span>
            <h3>Surface what matters.</h3>
            <p>
              Prioritize potential impact with evidence, context, and clear
              explanations instead of black-box conjectures.
            </p>
            <div className="risk-preview">
              <span>
                <i /> Dependency path
              </span>
              <span>
                <i /> Test coverage gap
              </span>
              <span>
                <i /> API boundary
              </span>
            </div>
          </article>
        </div>
      </section>
    </>
  );
}
