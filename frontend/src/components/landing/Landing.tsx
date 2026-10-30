import { LandingNav } from './LandingNav';
import { Hero } from './Hero';
import { FeatureGrid } from './FeatureGrid';
import { HowItWorks } from './HowItWorks';
import { LandingFooter } from './LandingFooter';
import { User } from '../../types';

interface LandingProps {
  currentUser?: User | null;
  onLaunch: () => void;
  onSignIn: () => void;
  onHome?: () => void;
}

export function Landing({ currentUser, onLaunch, onSignIn, onHome }: LandingProps) {
  return (
    <div className="landing">
      <LandingNav currentUser={currentUser} onLaunch={onLaunch} onSignIn={onSignIn} onHome={onHome} />
      <main>
        <Hero onLaunch={onLaunch} />
        <FeatureGrid />
        <HowItWorks onLaunch={onLaunch} />
      </main>
      <LandingFooter />
    </div>
  );
}
