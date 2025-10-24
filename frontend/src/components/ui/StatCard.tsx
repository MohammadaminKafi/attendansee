import React from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  iconColor?: string;
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({ 
  label, 
  value, 
  icon, 
  iconColor = 'text-primary',
  className = '' 
}) => {
  return (
    <div className={`bg-dark-card rounded-lg p-4 border border-dark-border hover:border-primary transition-colors ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-400 mb-1">{label}</p>
          <p className="text-2xl font-semibold text-gray-100">{value}</p>
        </div>
        {icon && (
          <div className={`text-3xl ${iconColor}`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
};
