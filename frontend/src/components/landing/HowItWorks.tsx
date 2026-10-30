import { ArrowRight, ArrowUpRight } from 'lucide-react';

export function HowItWorks({ onLaunch }: { onLaunch: () => void }) {
  return (
    <>
      <section className="manifesto" id="how">
        <div className="wrap manifesto-inner">
          <div className="eyebrow">
            <span className="eyebrow-dot" />
            <span>HOW THE ANALYSIS ENGINE WORKS</span>
          </div>
          <h2>
            From a code change
            <br />
            to a clearer <em>decision.</em>
          </h2>

          <div className="steps">
            <div className="step-card">
              <span className="step-num">01</span>
              <h3>Connect</h3>
              <p>
                Point ChangeRadar to a repository revision. The engine parses Python AST
                abstract syntax trees to extract all function, method, and class definitions
                without executing project code.
              </p>
            </div>

            <div className="step-card">
              <span className="step-num">02</span>
              <h3>Compare</h3>
              <p>
                Select a pull request or commit SHA. ChangeRadar isolates changed symbols
                against base revisions and traverses the dependency graph to find all direct
                and indirect consumers.
              </p>
            </div>

            <div className="step-card">
              <span className="step-num">03</span>
              <h3>Understand</h3>
              <p>
                Receive an explainable impact report mapping the exact chain of calls from
                modified symbols to downstream services, with prioritized test suites to run
                before merging.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="closing wrap" id="principles">
        <div className="closing-content">
          <div className="eyebrow">
            <span className="eyebrow-dot" />
            <span>ENGINEERING WITH REPRODUCIBLE CONTEXT</span>
          </div>
          <h2>
            Ship with your eyes
            <br />
            wide <em>open.</em>
          </h2>
          <p className="closing-lede">
            Give developers and reviewers the change intelligence they need to move fast
            without breaking dependencies.
          </p>
        </div>
        <div className="closing-actions">
          <button
            className="button button-lime button-hero"
            onClick={onLaunch}
            type="button"
          >
            <span>Launch workspace preview</span>
            <ArrowRight size={17} />
          </button>
        </div>
      </section>
    </>
  );
}
