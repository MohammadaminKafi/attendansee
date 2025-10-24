import { type ClassValue, clsx } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(date);
}

export function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export function getErrorMessage(error: unknown): string {
  if (typeof error === 'string') return error;
  
  if (error && typeof error === 'object') {
    if ('detail' in error && typeof error.detail === 'string') {
      return error.detail;
    }
    
    // Handle field-specific errors
    const errorObj = error as Record<string, unknown>;
    const firstKey = Object.keys(errorObj)[0];
    if (firstKey && errorObj[firstKey]) {
      const value = errorObj[firstKey];
      if (Array.isArray(value)) {
        return value[0];
      }
      if (typeof value === 'string') {
        return value;
      }
    }
  }
  
  return 'An unexpected error occurred';
}
