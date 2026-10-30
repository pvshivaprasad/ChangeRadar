import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, Github, LockKeyhole, X } from 'lucide-react';

interface ConnectRepoModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ConnectRepoModal({ isOpen, onClose }: ConnectRepoModalProps) {
  const [repoUrl, setRepoUrl] = useState('');
  const [notice, setNotice] = useState('');

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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) {
      setNotice('Please enter a GitHub repository URL.');
      return;
    }
    // Honest product status
    setNotice(
      'GitHub repository scanning engine is scheduled for Milestone 2. No repository was linked.'
    );
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
          >
            <div className="modal-head">
              <div className="modal-icon">
                <Github size={21} />
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

            <span className="eyebrow">REPOSITORY INTEGRATION</span>
            <h2 id="modal-title">
              Bring your code
              <br />
              <em>into context.</em>
            </h2>
            <p>
              Connect a public GitHub repository to get started. Private repository
              authorization will be enabled with the GitHub App integration.
            </p>

            <form onSubmit={handleSubmit}>
              <label htmlFor="repo-url">GitHub repository URL</label>
              <input
                id="repo-url"
                type="url"
                value={repoUrl}
                onChange={(e) => {
                  setRepoUrl(e.target.value);
                  setNotice('');
                }}
                placeholder="https://github.com/owner/repository"
                autoFocus
              />

              <div className="modal-note">
                <LockKeyhole size={13} /> Read-only access is enforced by default.
              </div>

              {notice && <div className="inline-notice">{notice}</div>}

              <button className="button button-lime modal-submit" type="submit">
                Continue <ArrowRight size={16} />
              </button>

              <button
                className="modal-cancel"
                onClick={onClose}
                type="button"
              >
                Cancel
              </button>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
