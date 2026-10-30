import React, { useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  Boxes,
  Braces,
  Check,
  Eye,
  EyeOff,
  GitBranch,
  Github,
  LockKeyhole,
  Radar,
  ShieldCheck,
  Sparkles,
  Workflow,
  Zap,
} from 'lucide-react';
import { Brand } from '../ui/Brand';

interface AuthPageProps {
  onSuccess: () => void;
  onBack: () => void;
  initialMode?: 'signin' | 'signup';
}

export function AuthPage({ onSuccess, onBack, initialMode = 'signin' }: AuthPageProps) {
  const [mode, setMode] = useState<'signin' | 'signup'>(initialMode);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [notice, setNotice] = useState<{ type: 'info' | 'error'; text: string } | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setNotice(null);

    if (!email.trim() || !password.trim()) {
      setNotice({ type: 'error', text: 'Please enter both your work email and password.' });
      return;
    }

    if (mode === 'signup' && !name.trim()) {
      setNotice({ type: 'error', text: 'Please enter your name to create an account.' });
      return;
    }

    setIsLoading(true);

    // Provide authentic interaction feedback without pretending a real auth backend exists yet
    setTimeout(() => {
      setIsLoading(false);
      // Log in as workspace preview user
      onSuccess();
    }, 600);
  };

  const handleOAuthClick = (provider: string) => {
    setNotice({
      type: 'info',
      text: `${provider} OAuth is scheduled for the GitHub App integration milestone. Use email to enter the preview workspace.`,
    });
  };

  return (
    <div className="auth-shell">
      {/* Visual Brand Column (Left on Desktop) */}
      <div className="auth-hero-pane">
        <div className="auth-hero-content">
          <div className="auth-brand-row">
            <button className="auth-back-btn" onClick={onBack} type="button">
              <ArrowLeft size={16} />
              <span>Back to home</span>
            </button>
            <Brand light size="md" />
          </div>

          <div className="auth-hero-copy">
            <div className="auth-hero-badge">
              <Sparkles size={14} /> ENTERPRISE CHANGE INTELLIGENCE
            </div>
            <h2>
              See the ripple effect
              <br />
              before you <em>merge.</em>
            </h2>
            <p>
              Connect repositories, surface breaking contract changes, and give
              your engineering team the confidence to ship faster with zero guesswork.
            </p>
          </div>

          {/* Interactive Hero Graph Graphic */}
          <div className="auth-art-card">
            <div className="auth-art-header">
              <span>LIVE IMPACT MAP</span>
              <span className="live-indicator">
                <i /> MONITORING
              </span>
            </div>

            <div className="auth-graph-canvas">
              <svg className="auth-graph-svg" viewBox="0 0 460 260" preserveAspectRatio="xMidYMid meet">
                <path d="M230 130 L110 65 M230 130 L350 65 M230 130 L120 200 M230 130 L340 200" stroke="#48543f" strokeWidth="1.5" strokeDasharray="3 4" fill="none" />
                <path d="M230 130 L110 65 M230 130 L350 65" stroke="#a4ce55" strokeWidth="2" fill="none" />
              </svg>

              <div className="auth-node node-center">
                <Braces size={16} />
                <b>core.auth</b>
                <small>CHANGED</small>
              </div>

              <div className="auth-node node-nw">
                <Boxes size={14} />
                <span>checkout</span>
              </div>

              <div className="auth-node node-ne">
                <Zap size={14} />
                <span>billing</span>
              </div>

              <div className="auth-node node-sw">
                <LockKeyhole size={14} />
                <span>sessions</span>
              </div>

              <div className="auth-node node-se">
                <GitBranch size={14} />
                <span>profile</span>
              </div>
            </div>

            <div className="auth-art-footer">
              <div className="auth-stat">
                <b>4</b>
                <span>Impacted modules</span>
              </div>
              <div className="auth-stat">
                <b>100%</b>
                <span>Graph provenance</span>
              </div>
              <div className="auth-stat">
                <b>0</b>
                <span>Broken builds</span>
              </div>
            </div>
          </div>

          <div className="auth-hero-footer">
            <span>Trusted by forward-thinking engineering leads</span>
            <div className="auth-pills">
              <span>Python AST</span>
              <span>FastAPI</span>
              <span>Call Graphs</span>
            </div>
          </div>
        </div>
      </div>

      {/* Auth Form Column (Right on Desktop) */}
      <div className="auth-form-pane">
        <div className="auth-form-card">
          <div className="auth-form-head">
            <div className="mobile-brand-row">
              <Brand size="md" />
              <button className="auth-back-btn mobile-only" onClick={onBack} type="button">
                <ArrowLeft size={16} /> Back
              </button>
            </div>
            <h1>{mode === 'signin' ? 'Welcome back' : 'Create your workspace'}</h1>
            <p className="auth-subtitle">
              {mode === 'signin'
                ? 'Sign in to access your change impact intelligence workspace.'
                : 'Start understanding your codebase dependencies in minutes.'}
            </p>
          </div>

          {/* Social Logins */}
          <div className="oauth-buttons">
            <button
              className="oauth-button"
              onClick={() => handleOAuthClick('GitHub')}
              type="button"
            >
              <Github size={18} />
              <span>Continue with GitHub</span>
            </button>
            <button
              className="oauth-button"
              onClick={() => handleOAuthClick('Google')}
              type="button"
            >
              <svg width="18" height="18" viewBox="0 0 24 24">
                <path
                  fill="#EA4335"
                  d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.7 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.4 9 5 12 5z"
                />
                <path
                  fill="#4285F4"
                  d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.8z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.6 14.8c-.2-.7-.4-1.5-.4-2.3s.2-1.6.4-2.3L1.9 7.3C.7 9.7 0 10.8 0 12.5s.7 2.8 1.9 5.2l3.7-2.9z"
                />
                <path
                  fill="#34A853"
                  d="M12 24c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.4-6.4-5.2L1.9 17C3.7 20.7 7.5 24 12 24z"
                />
              </svg>
              <span>Continue with Google</span>
            </button>
          </div>

          <div className="auth-divider">
            <span>or continue with email</span>
          </div>

          {notice && (
            <div className={`auth-notice auth-notice-${notice.type}`}>
              {notice.text}
            </div>
          )}

          <form onSubmit={handleSubmit} className="auth-form">
            {mode === 'signup' && (
              <div className="form-group">
                <label htmlFor="auth-name">Full name</label>
                <input
                  id="auth-name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Shiva Prasad"
                  required
                />
              </div>
            )}

            <div className="form-group">
              <label htmlFor="auth-email">Work email address</label>
              <input
                id="auth-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                required
              />
            </div>

            <div className="form-group">
              <div className="label-row">
                <label htmlFor="auth-password">Password</label>
                {mode === 'signin' && (
                  <button
                    type="button"
                    className="forgot-link"
                    onClick={() =>
                      setNotice({
                        type: 'info',
                        text: 'Password recovery will be enabled with production SMTP configuration.',
                      })
                    }
                  >
                    Forgot password?
                  </button>
                )}
              </div>
              <div className="password-input-wrap">
                <input
                  id="auth-password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                />
                <button
                  type="button"
                  className="eye-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {mode === 'signin' && (
              <div className="checkbox-row">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                  />
                  <span>Remember this device for 30 days</span>
                </label>
              </div>
            )}

            <button
              className="button button-lime auth-submit-btn"
              type="submit"
              disabled={isLoading}
            >
              {isLoading ? (
                <span>Entering workspace...</span>
              ) : mode === 'signin' ? (
                <>
                  <span>Sign in to ChangeRadar</span>
                  <ArrowRight size={17} />
                </>
              ) : (
                <>
                  <span>Create engineering workspace</span>
                  <ArrowRight size={17} />
                </>
              )}
            </button>
          </form>

          <div className="auth-switch-row">
            {mode === 'signin' ? (
              <p>
                Don't have an account?{' '}
                <button
                  className="switch-mode-btn"
                  onClick={() => {
                    setMode('signup');
                    setNotice(null);
                  }}
                  type="button"
                >
                  Create one now
                </button>
              </p>
            ) : (
              <p>
                Already have a workspace?{' '}
                <button
                  className="switch-mode-btn"
                  onClick={() => {
                    setMode('signin');
                    setNotice(null);
                  }}
                  type="button"
                >
                  Sign in
                </button>
              </p>
            )}
          </div>

          <div className="auth-footnote">
            <span>By proceeding, you agree to ChangeRadar's</span>{' '}
            <a href="#principles">Principles</a> & <a href="#privacy">Terms of Service</a>.
          </div>
        </div>
      </div>
    </div>
  );
}
