import React from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  caption?: string;
  icon?: React.ReactNode;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  caption,
  icon,
  className = '',
}) => {
  return (
    <div
      className={`
        bg-[var(--color-surface)] rounded-[24px] border border-[var(--color-border-subtle)] p-6
        shadow-card hover:shadow-card-hover hover:-translate-y-0.5
        transition-all duration-200 ease-out
        hover:border-primary/40
        ${className}
      `}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <p className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-secondary)] mb-2">
            {title}
          </p>
          <p className="text-3xl font-bold text-[var(--color-text-primary)] mb-1">
            {value}
          </p>
          {caption && (
            <p className="text-sm text-[var(--color-text-secondary)]">
              {caption}
            </p>
          )}
        </div>
        {icon && (
          <div className="ml-4 text-primary opacity-60">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
};

