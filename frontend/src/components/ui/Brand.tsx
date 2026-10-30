import { Radar } from 'lucide-react';

interface BrandProps {
  light?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function Brand({ light = false, size = 'md', className = '' }: BrandProps) {
  const markSizes = {
    sm: { box: 26, icon: 15 },
    md: { box: 34, icon: 19 },
    lg: { box: 42, icon: 24 },
  };

  const current = markSizes[size];

  return (
    <div className={`brand brand-${size} ${light ? 'brand-light' : ''} ${className}`}>
      <span
        className="brand-mark"
        style={{ width: `${current.box}px`, height: `${current.box}px` }}
      >
        <Radar size={current.icon} strokeWidth={2.2} />
      </span>
      <span className="brand-text">
        <span className="brand-prefix">change</span>
        <span className="brand-strong">radar</span>
      </span>
    </div>
  );
}
