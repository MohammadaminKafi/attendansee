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
  iconColor = 'text-blue-500',
  className = '' 
}) => {
  return (
    <div className={`bg-slate-800 rounded-lg p-4 border border-slate-700 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm text-slate-400 mb-1">{label}</p>
          <p className="text-2xl font-semibold text-slate-100">{value}</p>
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
