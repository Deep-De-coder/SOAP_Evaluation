import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'neutral';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ 
  children, 
  variant = 'default',
  className = '' 
}) => {
  const variantClasses = {
    default: 'bg-gray-100 text-gray-800',
    success: 'bg-green-50 text-green-700 border border-green-200',
    warning: 'bg-orange-50 text-badge-warning border border-orange-200',
    error: 'bg-red-50 text-badge-danger border border-red-200',
    info: 'bg-blue-50 text-badge-info border border-blue-200',
    neutral: 'bg-gray-50 text-[var(--color-text-secondary)] border border-[var(--color-border-subtle)]',
  };

  return (
    <span
      className={`
        inline-flex items-center px-3 py-1 rounded-full 
        text-xs font-medium border
        ${variantClasses[variant]} 
        ${className}
      `}
    >
      {children}
    </span>
  );
};
