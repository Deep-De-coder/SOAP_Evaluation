import React from 'react';

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  className?: string;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  subtitle,
  className = '',
}) => {
  return (
    <div className={`mb-8 ${className}`}>
      <h2 className="text-2xl font-semibold text-[var(--color-text-primary)] mb-2">
        {title}
      </h2>
      {subtitle && (
        <p className="text-sm text-[var(--color-text-secondary)]">
          {subtitle}
        </p>
      )}
    </div>
  );
};

