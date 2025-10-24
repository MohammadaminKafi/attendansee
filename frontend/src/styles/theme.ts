/**
 * Centralized Theme Configuration
 * All color classes and styling constants in one place for easy maintenance
 */

export const theme = {
  // Background colors
  bg: {
    primary: 'bg-dark-bg',
    card: 'bg-dark-card',
    hover: 'bg-dark-hover',
  },
  
  // Border colors
  border: {
    default: 'border-dark-border',
    light: 'border-dark-light',
    primary: 'border-primary',
    success: 'border-success',
    warning: 'border-warning',
    danger: 'border-danger',
  },
  
  // Text colors
  text: {
    primary: 'text-gray-100',
    secondary: 'text-gray-300',
    tertiary: 'text-gray-400',
    muted: 'text-gray-500',
    accent: 'text-primary',
    accentHover: 'text-primary-light',
    success: 'text-success',
    warning: 'text-warning',
    danger: 'text-danger',
  },
  
  // Interactive colors
  interactive: {
    primary: 'text-primary hover:text-primary-light',
    primaryBg: 'bg-primary hover:bg-primary-hover',
    success: 'text-success hover:text-success-light',
    warning: 'text-warning hover:text-warning-light',
    danger: 'text-danger hover:text-danger-light',
  },
  
  // Common component classes
  components: {
    card: 'bg-dark-card border border-dark-border rounded-lg',
    cardHover: 'bg-dark-card border border-dark-border rounded-lg hover:border-primary transition-colors',
    input: 'bg-dark-card border border-dark-border text-gray-100 focus:ring-primary focus:border-primary',
    table: {
      header: 'bg-dark-card border-b border-dark-border',
      row: 'bg-dark-card hover:bg-dark-hover transition-colors',
      cell: 'text-gray-300',
      divide: 'divide-dark-border',
    },
  },
  
  // Transitions
  transition: {
    default: 'transition-colors duration-200',
    fast: 'transition-all duration-150',
    slow: 'transition-all duration-300',
  },
} as const;

// Helper functions for combining classes
export const cn = (...classes: (string | undefined | null | false)[]) => {
  return classes.filter(Boolean).join(' ');
};
