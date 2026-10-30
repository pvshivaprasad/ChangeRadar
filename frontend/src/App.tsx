import { useEffect, useState } from 'react';
import { Landing } from './components/landing/Landing';
import { Workspace } from './components/workspace/Workspace';
import { AuthPage } from './components/auth/AuthPage';
import {
  clearAuthToken,
  fetchCurrentUser,
  getAuthToken,
  getCachedUser,
  logoutUser,
  setCachedUser,
} from './api/client';
import { User } from './types';
import { Radar } from 'lucide-react';

export type AppView = 'landing' | 'workspace' | 'auth';

function getViewFromHash(): AppView {
  const hash = window.location.hash.toLowerCase().replace('#', '');
  if (hash === 'workspace') return 'workspace';
  if (hash === 'auth' || hash === 'signin' || hash === 'login') return 'auth';
  return 'landing';
}

export default function App() {
  const [view, setView] = useState<AppView>(getViewFromHash);
  const [user, setUser] = useState<User | null>(getCachedUser);
  const [isAuthChecking, setIsAuthChecking] = useState<boolean>(true);
  const [authNotice, setAuthNotice] = useState<string | null>(null);

  // 1. Initial Session Check (Validates session with backend while avoiding UI flicker)
  useEffect(() => {
    let isMounted = true;
    async function checkSession() {
      try {
        const currentUser = await fetchCurrentUser();
        if (isMounted) {
          if (currentUser) {
            setUser(currentUser);
            setCachedUser(currentUser, true);
          } else {
            setUser(null);
          }
        }
      } catch {
        if (isMounted) setUser(null);
      } finally {
        if (isMounted) setIsAuthChecking(false);
      }
    }
    checkSession();
    return () => {
      isMounted = false;
    };
  }, []);

  // 2. Hash routing sync and browser history back/forward support
  useEffect(() => {
    function handleHashChange() {
      const targetView = getViewFromHash();
      setView(targetView);
    }
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const navigateTo = (newView: AppView, notice?: string) => {
    if (notice) setAuthNotice(notice);
    setView(newView);
    window.location.hash = newView;
  };

  const handleLoginSuccess = (loggedInUser: User) => {
    setUser(loggedInUser);
    setAuthNotice(null);
    window.history.replaceState(null, '', '#workspace');
    setView('workspace');
    window.location.hash = 'workspace';
  };

  const handleLogout = async () => {
    await logoutUser();
    setUser(null);
    window.history.replaceState(null, '', '#landing');
    setView('landing');
    window.location.hash = 'landing';
  };

  const handleLaunchWorkspace = () => {
    if (user || getAuthToken()) {
      navigateTo('workspace');
    } else {
      navigateTo('auth', 'Please sign in to access your ChangeRadar workspace.');
    }
  };

  // Protected route loading state (prevents authentication flicker)
  if (view === 'workspace' && isAuthChecking && !user && getAuthToken()) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          backgroundColor: 'var(--ws-bg)',
          color: 'var(--ws-text)',
          gap: '16px',
        }}
      >
        <div
          style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            backgroundColor: 'var(--lime)',
            display: 'grid',
            placeItems: 'center',
            color: '#171916',
            boxShadow: '0 0 20px rgba(199, 243, 107, 0.4)',
            animation: 'pulse 1.8s infinite ease-in-out',
          }}
        >
          <Radar size={28} />
        </div>
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--ws-text-muted)' }}>
          Validating workspace session...
        </p>
      </div>
    );
  }

  // Protected route enforcement
  if (view === 'workspace' && !isAuthChecking && !user && !getAuthToken()) {
    return (
      <AuthPage
        onSuccess={handleLoginSuccess}
        onBack={() => navigateTo('landing')}
        initialNotice={authNotice || 'Please sign in to access your ChangeRadar workspace.'}
      />
    );
  }

  if (view === 'auth') {
    return (
      <AuthPage
        onSuccess={handleLoginSuccess}
        onBack={() => navigateTo('landing')}
        initialNotice={authNotice || undefined}
      />
    );
  }

  if (view === 'workspace') {
    return (
      <Workspace
        currentUser={user}
        onHome={() => navigateTo('landing')}
        onLogout={handleLogout}
      />
    );
  }

  return (
    <Landing
      currentUser={user}
      onLaunch={handleLaunchWorkspace}
      onSignIn={() => navigateTo('auth')}
      onHome={() => navigateTo('landing')}
    />
  );
}
