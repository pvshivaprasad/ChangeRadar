import { LandingNav } from './LandingNav';
import { Hero } from './Hero';
import { FeatureGrid } from './FeatureGrid';
import { HowItWorks } from './HowItWorks';
import { LandingFooter } from './LandingFooter';

interface LandingProps {
  onLaunch: () => void;
  onSignIn: () => void;
}

export function Landing({ onLaunch, onSignIn }: LandingProps) {
  return (
    <div className="landing">
      <LandingNav onLaunch={onLaunch} onSignIn={onSignIn} />
      <main>
        <Hero onLaunch={onLaunch} />
        <FeatureGrid />
        <HowItWorks onLaunch={onLaunch} />
      </main>
      <LandingFooter />
    </div>
  );
}
