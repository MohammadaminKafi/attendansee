import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'success' | 'warning' | 'error' | 'info' | 'default';
  className?: string;
}

const variantStyles = {
  success: 'bg-success/20 text-success-light ring-success/40 shadow-success/10',
  warning: 'bg-warning/20 text-warning-light ring-warning/40 shadow-warning/10',
  error: 'bg-danger/20 text-danger-light ring-danger/40 shadow-danger/10',
  info: 'bg-primary/20 text-primary-light ring-primary/40 shadow-primary/10',
  default: 'bg-dark-light/30 text-gray-300 ring-dark-border shadow-dark-light/10',
};

export const Badge: React.FC<BadgeProps> = ({ 
  children, 
  variant = 'default', 
  className = '' 
}) => {
  return (
    <span
      className={`
        inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
        ring-1 ring-inset shadow-sm
        ${variantStyles[variant]}
        ${className}
      `}
    >
      {children}
    </span>
  );
};
