import { ArrowUpRight } from 'lucide-react';

export function HowItWorks({ onLaunch }: { onLaunch: () => void }) {
  return (
    <>
      <section className="manifesto" id="how">
        <div className="wrap manifesto-inner">
          <div className="eyebrow">HOW IT WORKS</div>
          <h2>
            From a code change
            <br />
            to a clearer <em>decision.</em>
          </h2>
          <div className="steps">
            <div>
              <b>01</b>
              <h3>Connect</h3>
              <p>
                Point to a repository and let ChangeRadar extract symbols and
                build its statically verified dependency map.
              </p>
            </div>
            <div>
              <b>02</b>
              <h3>Compare</h3>
              <p>
                Select a commit or pull request to isolate exact symbol diffs and
                affected call chains.
              </p>
            </div>
            <div>
              <b>03</b>
              <h3>Understand</h3>
              <p>
                Review affected downstream paths, prioritized test suites, and
                evidence-backed risk findings.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="closing wrap" id="principles">
        <div>
          <div className="eyebrow">ENGINEERING, WITH CONTEXT</div>
          <h2>
            Ship with your eyes
            <br />
            wide <em>open.</em>
          </h2>
        </div>
        <button
          className="button button-dark"
          onClick={onLaunch}
          type="button"
        >
          Explore ChangeRadar <ArrowUpRight size={17} />
        </button>
      </section>
    </>
  );
}
