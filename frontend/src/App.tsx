import { useState } from 'react';
import { Landing } from './components/landing/Landing';
import { Workspace } from './components/workspace/Workspace';

export default function App() {
  const [inWorkspace, setInWorkspace] = useState(false);

  return inWorkspace ? (
    <Workspace onHome={() => setInWorkspace(false)} />
  ) : (
    <Landing onLaunch={() => setInWorkspace(true)} />
  );
}
