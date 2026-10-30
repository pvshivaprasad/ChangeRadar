import React, { useState } from 'react';
import {
  AlertCircle,
  ArrowRight,
  Check,
  CheckCircle2,
  Copy,
  ExternalLink,
  FileCode,
  Flame,
  Info,
  Sparkles,
  TestTube2,
  Zap,
} from 'lucide-react';
import { ImpactAnalysisReport, TestRecommendation } from '../../../types';

interface WhatToTestSectionProps {
  report: ImpactAnalysisReport;
}

export const WhatToTestSection: React.FC<WhatToTestSectionProps> = ({ report }) => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const copyCommand = (cmd: string, idx: number) => {
    navigator.clipboard.writeText(cmd);
    setCopiedIndex(idx);
    setTimeout(() => {
      setCopiedIndex(null);
    }, 2000);
  };

  const tests = report.recommended_tests;

  return (
    <section className="surface-card what-to-test-card">
      <div className="section-header-row">
        <div>
          <div className="section-eyebrow">
            <TestTube2 size={14} color="var(--violet)" />
            <span>TEST SUITE INTELLIGENCE</span>
          </div>
          <h3>What Should I Test?</h3>
          <p>
            Relevance-ranked test recommendations mapped directly to the code paths affected by this change.
          </p>
        </div>

        <div className="test-disclaimer-pill">
          <Info size={13} color="var(--ws-text-muted)" />
          <span>Recommended next actions (not pre-executed)</span>
        </div>
      </div>

      {tests.length === 0 ? (
        <div className="empty-tests-box">
          <CheckCircle2 size={28} color="var(--lime)" />
          <h4>No Direct Test Mapping Found</h4>
          <p>
            None of the existing test suites in the repository directly import or call the modified
            symbols. Consider adding regression tests for altered functions.
          </p>
        </div>
      ) : (
        <div className="recommended-tests-grid">
          {tests.map((test, idx) => {
            const isHighPriority = test.priority === 'high';
            const testFileName = test.test_file.split(/[\\/]/).pop();
            const targetSymbolShort = test.target_symbol_id.split('.').slice(-2).join('.');
            const testSymbolShort = test.test_symbol_id
              ? test.test_symbol_id.split('.').pop()
              : null;

            const runCommand = testSymbolShort
              ? `pytest ${test.test_file} -k "${testSymbolShort}"`
              : `pytest ${test.test_file}`;

            return (
              <div
                key={idx}
                className={`test-card-item ${isHighPriority ? 'priority-high' : 'priority-medium'}`}
              >
                <div className="test-card-header">
                  <div className="test-priority-tag">
                    {isHighPriority ? (
                      <>
                        <Flame size={13} color="#d66e68" />
                        <span className="priority-high-text">HIGH RELEVANCE</span>
                      </>
                    ) : (
                      <>
                        <Zap size={13} color="var(--amber)" />
                        <span className="priority-medium-text">MEDIUM RELEVANCE</span>
                      </>
                    )}
                  </div>
                  <span className="test-file-badge">{testFileName}</span>
                </div>

                <div className="test-card-body">
                  <div className="test-symbol-name">
                    <TestTube2 size={16} className="test-icon" />
                    <b>{testSymbolShort || 'Full Test Suite'}</b>
                  </div>
                  <div className="test-path-text">{test.test_file}</div>

                  {/* Triggering connection */}
                  <div className="test-trigger-box">
                    <span className="trigger-label">Triggered by change to:</span>
                    <div className="trigger-symbol">
                      <code>{targetSymbolShort}</code>
                      <small>({test.target_symbol_id})</small>
                    </div>
                  </div>

                  <p className="test-reason-text">{test.reason}</p>
                </div>

                <div className="test-card-footer">
                  <code className="test-cli-preview">{runCommand}</code>
                  <button
                    type="button"
                    className="copy-cli-btn"
                    onClick={() => copyCommand(runCommand, idx)}
                    title="Copy command to clipboard"
                  >
                    {copiedIndex === idx ? (
                      <>
                        <Check size={13} color="var(--lime)" />
                        <span>Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy size={13} />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
};
