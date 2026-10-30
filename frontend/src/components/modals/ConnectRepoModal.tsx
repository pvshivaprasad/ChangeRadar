import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, ArrowRight, CheckCircle2, FolderGit2, ShieldCheck, X } from 'lucide-react';
import { createRepository } from '../../api/client';
import { RepositoryRecord } from '../../types';

interface ConnectRepoModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportSuccess: (repo: RepositoryRecord) => void;
}

export function ConnectRepoModal({ isOpen, onClose, onImportSuccess }: ConnectRepoModalProps) {
  const [repoPath, setRepoPath] = useState('');
  const [repoName, setRepoName] = useState('');
  const [branch, setBranch] = useState('main');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorNotice, setErrorNotice] = useState<string | null>(null);

  // Handle ESC key
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorNotice(null);

    const cleanPath = repoPath.trim();
    if (!cleanPath) {
      setErrorNotice('Please provide a valid local repository directory path.');
      return;
    }

    setIsSubmitting(true);
    try {
      const repo = await createRepository(cleanPath, repoName.trim() || undefined, branch.trim() || 'main');
      setIsSubmitting(false);
      onImportSuccess(repo);
      onClose();
    } catch (err: unknown) {
      setIsSubmitting(false);
      const msg = err instanceof Error ? err.message : 'Failed to import repository.';
      setErrorNotice(msg);
    }
  };

  const handleQuickFill = (path: string, name: string) => {
    setRepoPath(path);
    setRepoName(name);
    setErrorNotice(null);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="modal-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.18 }}
          onClick={(e) => {
            if (e.target === e.currentTarget) onClose();
          }}
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-title"
        >
          <motion.div
            className="connect-modal"
            initial={{ opacity: 0, scale: 0.96, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 8 }}
            transition={{ duration: 0.18, ease: 'easeOut' }}
            style={{ maxWidth: '580px' }}
          >
            <div className="modal-head">
              <div className="modal-icon">
                <FolderGit2 size={22} color="var(--lime)" />
              </div>
              <button
                className="icon-button"
                onClick={onClose}
                aria-label="Close dialog"
                type="button"
              >
                <X size={18} />
              </button>
            </div>

            <span className="eyebrow">REPOSITORY IMPORT & SCAN</span>
            <h2 id="modal-title">
              Import local
              <br />
              <em>codebase.</em>
            </h2>
            <p>
              Point ChangeRadar to any Python repository on your local system. The engine
              statically indexes functions, methods, classes, and call dependencies.
            </p>

            <form onSubmit={handleSubmit} style={{ marginTop: '20px' }}>
              <div style={{ marginBottom: '16px' }}>
                <label htmlFor="repo-path" style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--ws-text)', marginBottom: '6px' }}>
                  Local Repository Directory Path <span style={{ color: 'var(--lime)' }}>*</span>
                </label>
                <input
                  id="repo-path"
                  type="text"
                  value={repoPath}
                  onChange={(e) => {
                    setRepoPath(e.target.value);
                    setErrorNotice(null);
                  }}
                  placeholder="e.g. D:\Movies\ScamShield-Polished-Deploy-Ready\scamshield"
                  autoFocus
                  required
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    borderRadius: '8px',
                    border: '1px solid var(--ws-border)',
                    background: 'var(--ws-surface)',
                    color: 'var(--ws-text)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '13px',
                  }}
                />
              </div>

              {/* Quick Fill Shortcuts for reviewer convenience */}
              <div style={{ marginBottom: '18px' }}>
                <span style={{ fontSize: '11px', color: 'var(--ws-text-faint)', display: 'block', marginBottom: '6px' }}>
                  QUICK FILL PRESETS:
                </span>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    onClick={() => handleQuickFill('D:\\Movies\\ChangeRadar-v0.1.1\\changeradar\\backend\\tests\\fixtures\\synthetic_repo', 'synthetic-payment-auth')}
                    style={{
                      fontSize: '11px',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      background: 'rgba(199, 243, 107, 0.1)',
                      border: '1px solid rgba(199, 243, 107, 0.25)',
                      color: 'var(--lime)',
                      cursor: 'pointer',
                    }}
                  >
                    + Synthetic Fixture
                  </button>
                  <button
                    type="button"
                    onClick={() => handleQuickFill('D:\\Movies\\ScamShield-Polished-Deploy-Ready\\scamshield', 'ScamShield Production')}
                    style={{
                      fontSize: '11px',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      background: 'rgba(166, 155, 234, 0.12)',
                      border: '1px solid rgba(166, 155, 234, 0.25)',
                      color: 'var(--violet)',
                      cursor: 'pointer',
                    }}
                  >
                    + ScamShield Workspace
                  </button>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '14px', marginBottom: '16px' }}>
                <div>
                  <label htmlFor="repo-name" style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--ws-text)', marginBottom: '6px' }}>
                    Display Name (Optional)
                  </label>
                  <input
                    id="repo-name"
                    type="text"
                    value={repoName}
                    onChange={(e) => setRepoName(e.target.value)}
                    placeholder="e.g. billing-service"
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: '8px',
                      border: '1px solid var(--ws-border)',
                      background: 'var(--ws-surface)',
                      color: 'var(--ws-text)',
                      fontSize: '13px',
                    }}
                  />
                </div>
                <div>
                  <label htmlFor="repo-branch" style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--ws-text)', marginBottom: '6px' }}>
                    Default Branch
                  </label>
                  <input
                    id="repo-branch"
                    type="text"
                    value={branch}
                    onChange={(e) => setBranch(e.target.value)}
                    placeholder="main"
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: '8px',
                      border: '1px solid var(--ws-border)',
                      background: 'var(--ws-surface)',
                      color: 'var(--ws-text)',
                      fontSize: '13px',
                    }}
                  />
                </div>
              </div>

              {errorNotice && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f28b85', fontSize: '13px', margin: '12px 0' }}>
                  <AlertCircle size={16} />
                  <span>{errorNotice}</span>
                </div>
              )}

              <div style={{ marginTop: '20px', display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  className="button button-ghost"
                  onClick={onClose}
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="button button-lime"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Scanning & Persisting...' : 'Scan & Import Repository'}
                  <ArrowRight size={16} />
                </button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
