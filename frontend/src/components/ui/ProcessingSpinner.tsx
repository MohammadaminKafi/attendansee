import React from 'react';
import { Loader2 } from 'lucide-react';

interface ProcessingSpinnerProps {
  message?: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const ProcessingSpinner: React.FC<ProcessingSpinnerProps> = ({
  message = 'Processing...',
  className = '',
  size = 'md',
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  const textSizes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  return (
    <div className={`flex flex-col items-center justify-center gap-3 ${className}`}>
      <div className="relative">
        {/* Outer ring */}
        <div className="absolute inset-0 rounded-full border-4 border-primary/20"></div>
        {/* Spinning icon */}
        <Loader2 className={`${sizeClasses[size]} text-primary animate-spin`} />
      </div>
      {message && (
        <p className={`${textSizes[size]} text-gray-300 font-medium animate-pulse`}>
          {message}
        </p>
      )}
    </div>
  );
};

interface ProcessingOverlayProps {
  isProcessing: boolean;
  message?: string;
  progress?: {
    current: number;
    total: number;
  };
}

export const ProcessingOverlay: React.FC<ProcessingOverlayProps> = ({
  isProcessing,
  message = 'Processing...',
  progress,
}) => {
  if (!isProcessing) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-dark-card border border-dark-border rounded-lg p-8 max-w-md w-full mx-4 shadow-xl">
        <ProcessingSpinner message={message} size="lg" className="mb-4" />
        
        {progress && (
          <div className="mt-6">
            <div className="flex justify-between text-sm text-gray-400 mb-2">
              <span>Progress</span>
              <span>
                {progress.current} / {progress.total}
              </span>
            </div>
            <div className="w-full bg-dark-bg rounded-full h-2 overflow-hidden">
              <div
                className="bg-gradient-to-r from-primary to-primary-light h-full transition-all duration-300 ease-out"
                style={{
                  width: `${(progress.current / progress.total) * 100}%`,
                }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              {Math.round((progress.current / progress.total) * 100)}% complete
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

interface InlineProcessingProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const InlineProcessing: React.FC<InlineProcessingProps> = ({
  message = 'Processing...',
  size = 'sm',
}) => {
  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  return (
    <div className="inline-flex items-center gap-2">
      <Loader2 className={`${iconSizes[size]} text-primary animate-spin`} />
      <span className="text-sm text-gray-300">{message}</span>
    </div>
  );
};
