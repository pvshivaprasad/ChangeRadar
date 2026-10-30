import { useEffect, useState } from 'react';
import { Landing } from './components/landing/Landing';
import { Workspace } from './components/workspace/Workspace';
import { AuthPage } from './components/auth/AuthPage';
import { clearAuthToken, fetchCurrentUser } from './api/client';
import { User } from './types';

export type AppView = 'landing' | 'workspace' | 'auth';

function getViewFromHash(): AppView {
  const hash = window.location.hash.toLowerCase().replace('#', '');
  if (hash === 'workspace') return 'workspace';
  if (hash === 'auth' || hash === 'signin' || hash === 'login') return 'auth';
  return 'landing';
}

export default function App() {
  const [view, setView] = useState<AppView>(getViewFromHash);
  const [user, setUser] = useState<User | null>(null);
  const [isAuthChecking, setIsAuthChecking] = useState<boolean>(true);
  const [authNotice, setAuthNotice] = useState<string | null>(null);

  // 1. Initial Session Check (persists login after page refresh)
  useEffect(() => {
    let isMounted = true;
    async function checkSession() {
      try {
        const currentUser = await fetchCurrentUser();
        if (isMounted) {
          if (currentUser) {
            setUser(currentUser);
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
    navigateTo('workspace');
  };

  const handleLogout = () => {
    clearAuthToken();
    setUser(null);
    navigateTo('landing');
  };

  const handleLaunchWorkspace = () => {
    if (!user) {
      navigateTo('auth', 'Please sign in to access your ChangeRadar workspace.');
    } else {
      navigateTo('workspace');
    }
  };

  // Protected route enforcement
  if (view === 'workspace' && !isAuthChecking && !user) {
    return (
      <AuthPage
        onSuccess={handleLoginSuccess}
        onBack={() => navigateTo('landing')}
        initialNotice="Please sign in to access your ChangeRadar workspace."
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
      onLaunch={handleLaunchWorkspace}
      onSignIn={() => navigateTo('auth')}
      onHome={() => navigateTo('landing')}
    />
  );
}
