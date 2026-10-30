import { useState } from 'react';
import { Landing } from './components/landing/Landing';
import { Workspace } from './components/workspace/Workspace';
import { AuthPage } from './components/auth/AuthPage';

export type AppView = 'landing' | 'workspace' | 'auth';

export default function App() {
  const [view, setView] = useState<AppView>('landing');

  if (view === 'auth') {
    return (
      <AuthPage
        onSuccess={() => setView('workspace')}
        onBack={() => setView('landing')}
      />
    );
  }

  if (view === 'workspace') {
    return (
      <Workspace
        onHome={() => setView('landing')}
        onAuth={() => setView('auth')}
      />
    );
  }

  return (
    <Landing
      onLaunch={() => setView('workspace')}
      onSignIn={() => setView('auth')}
    />
  );
}
