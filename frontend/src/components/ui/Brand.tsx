import { Radar } from 'lucide-react';

interface BrandProps {
  light?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function Brand({ light = false, size = 'md', className = '' }: BrandProps) {
  const markSizes = {
    sm: { box: 28, icon: 16 },
    md: { box: 34, icon: 19 },
    lg: { box: 44, icon: 26 },
  };

  const current = markSizes[size];

  return (
    <div className={`brand brand-${size} ${light ? 'brand-light' : ''} ${className}`}>
      <span
        className="brand-mark"
        style={{ width: `${current.box}px`, height: `${current.box}px` }}
        aria-hidden="true"
      >
        <Radar size={current.icon} strokeWidth={2.4} />
      </span>
      <span className="brand-text">
        <span className="brand-prefix">Change</span>
        <span className="brand-strong">Radar</span>
      </span>
    </div>
  );
}
