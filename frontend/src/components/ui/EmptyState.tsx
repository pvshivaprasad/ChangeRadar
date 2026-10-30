import React from 'react';
import { ArrowRight, Radar } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  action?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export function EmptyState({
  title,
  description,
  action,
  onAction,
  icon,
}: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-icon">
        {icon || <Radar size={24} strokeWidth={1.8} />}
      </div>
      <h3>{title}</h3>
      <p>{description}</p>
      {action && (
        <button
          className="button button-lime button-small"
          onClick={onAction}
          type="button"
        >
          {action} <ArrowRight size={14} />
        </button>
      )}
    </div>
  );
}
