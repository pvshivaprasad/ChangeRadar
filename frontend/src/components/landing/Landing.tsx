import { LandingNav } from './LandingNav';
import { Hero } from './Hero';
import { FeatureGrid } from './FeatureGrid';
import { HowItWorks } from './HowItWorks';
import { LandingFooter } from './LandingFooter';

export function Landing({ onLaunch }: { onLaunch: () => void }) {
  return (
    <div className="landing">
      <LandingNav onLaunch={onLaunch} />
      <main>
        <Hero onLaunch={onLaunch} />
        <FeatureGrid />
        <HowItWorks onLaunch={onLaunch} />
      </main>
      <LandingFooter />
    </div>
  );
}
