import React, { useState } from 'react';
import {
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Compass,
  FileCode,
  GitBranch,
  HelpCircle,
  Play,
  Sparkles,
  TestTube2,
  Workflow,
  X,
} from 'lucide-react';

interface GuidedSampleTourProps {
  onRunSample: () => void;
  isAnalyzing: boolean;
  hasReport: boolean;
}

export const GuidedSampleTour: React.FC<GuidedSampleTourProps> = ({
  onRunSample,
  isAnalyzing,
  hasReport,
}) => {
  const [isOpen, setIsOpen] = useState(!hasReport);
  const [activeStep, setActiveStep] = useState(0);

  const steps = [
    {
      step: '01',
      title: 'Connect & Ingest',
      icon: <FileCode size={16} color="var(--lime)" />,
      description:
        'ChangeRadar scans your local Python repository using pure AST parsing. No repository code is ever executed.',
    },
    {
      step: '02',
      title: 'Compare Revisions',
      icon: <GitBranch size={16} color="var(--lime)" />,
      description:
        'Select two Git commit SHAs or branch refs. ChangeRadar detects exact lines and functions modified.',
    },
    {
      step: '03',
      title: 'Map Dependencies',
      icon: <Workflow size={16} color="var(--amber)" />,
      description:
        'NetworkX reverse-traverses the symbol graph to calculate direct callers and transitive ripple dependents.',
    },
    {
      step: '04',
      title: 'Prioritize Testing',
      icon: <TestTube2 size={16} color="var(--violet)" />,
      description:
        'Targeted tests are mapped directly to altered execution paths so you know exactly what to test before merging.',
    },
  ];

  return (
    <div className="surface-card guided-tour-container">
      <div className="guided-tour-header">
        <div className="tour-title-area" onClick={() => setIsOpen(!isOpen)} role="button" tabIndex={0}>
          <div className="tour-badge">
            <Compass size={14} color="var(--lime)" />
            <span>FIRST-TIME DEVELOPER GUIDE</span>
          </div>
          <h3>How ChangeRadar Works</h3>
          <p className="tour-subtitle">
            Understand change impact in 4 steps: Change your code &bull; Understand its impact &bull; Know what to test.
          </p>
        </div>

        <div className="tour-actions-area">
          <button
            type="button"
            className="button button-lime tour-run-btn"
            onClick={onRunSample}
            disabled={isAnalyzing}
          >
            <Play size={14} />
            <span>{isAnalyzing ? 'Analyzing Sample...' : 'Try Sample Walkthrough'}</span>
          </button>
          <button
            type="button"
            className="tour-toggle-btn"
            onClick={() => setIsOpen(!isOpen)}
            aria-label={isOpen ? 'Collapse Guide' : 'Expand Guide'}
          >
            {isOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="guided-tour-content">
          <div className="tour-steps-grid">
            {steps.map((st, idx) => (
              <div
                key={st.step}
                className={`tour-step-card ${activeStep === idx ? 'step-active' : ''}`}
                onClick={() => setActiveStep(idx)}
              >
                <div className="tour-step-top">
                  <span className="tour-step-pill">{st.step}</span>
                  {st.icon}
                </div>
                <h4>{st.title}</h4>
                <p>{st.description}</p>
              </div>
            ))}
          </div>

          <div className="tour-footer-hint">
            <Sparkles size={14} color="var(--lime)" />
            <span>
              Tip: The <b>Sample Fixture</b> simulates a pull request modifying authentication token validation.
              Notice how callers in <code>checkout</code> and <code>payment</code> are automatically surfaced!
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
