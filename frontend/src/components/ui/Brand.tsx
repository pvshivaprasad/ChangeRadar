import { Radar } from 'lucide-react';

interface BrandProps {
  light?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function Brand({ light = false, size = 'md' }: BrandProps) {
  const markSize = size === 'sm' ? 16 : size === 'lg' ? 22 : 19;
  return (
    <div className={`brand ${light ? 'brand-light' : ''} brand-${size}`}>
      <span className="brand-mark">
        <Radar size={markSize} strokeWidth={2.2} />
      </span>
      <span>
        change<span className="brand-strong">radar</span>
      </span>
    </div>
  );
}
