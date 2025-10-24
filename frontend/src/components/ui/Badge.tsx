import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'success' | 'warning' | 'error' | 'info' | 'default';
  className?: string;
}

const variantStyles = {
  success: 'bg-green-900/30 text-green-400 ring-green-500/30',
  warning: 'bg-yellow-900/30 text-yellow-400 ring-yellow-500/30',
  error: 'bg-red-900/30 text-red-400 ring-red-500/30',
  info: 'bg-blue-900/30 text-blue-400 ring-blue-500/30',
  default: 'bg-slate-700/50 text-slate-300 ring-slate-600/30',
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
        ring-1 ring-inset
        ${variantStyles[variant]}
        ${className}
      `}
    >
      {children}
    </span>
  );
};
