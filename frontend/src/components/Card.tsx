import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}

export const Card: React.FC<CardProps> = ({ 
  children, 
  className = '',
  hover = false,
}) => {
  const hoverClasses = hover
    ? 'hover:shadow-card-hover hover:-translate-y-0.5 hover:border-primary/40 transition-all duration-200 ease-out'
    : '';

  return (
    <div
      className={`
        bg-[var(--color-surface)] rounded-[24px] border border-[var(--color-border-subtle)] p-6
        shadow-card ${hoverClasses}
        ${className}
      `}
    >
      {children}
    </div>
  );
};

interface CardHeaderProps {
  title: string;
  subtitle?: string;
}

export const CardHeader: React.FC<CardHeaderProps> = ({ title, subtitle }) => {
  return (
    <div className="mb-6">
      <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-1">{title}</h3>
      {subtitle && (
        <p className="text-sm text-[var(--color-text-secondary)] mt-1">{subtitle}</p>
      )}
    </div>
  );
};
