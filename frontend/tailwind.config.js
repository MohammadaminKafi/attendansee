/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: '#080e08',      // Very dark background
          card: '#0e180e',    // Slightly lighter for cards
          hover: '#283028',   // Hover state
          border: '#283828',  // Subtle borders
          light: '#388838',   // Lighter elements
        },
        primary: {
          DEFAULT: '#10b981', // Emerald green
          hover: '#059669',   // Darker green on hover
          light: '#34d399',   // Lighter green
          dark: '#047857',    // Darkest green
        },
        success: {
          DEFAULT: '#10b981', // Same as primary green
          light: '#34d399',
          dark: '#047857',
        },
        danger: {
          DEFAULT: '#dc2626', // Adjusted red to complement green
          light: '#ef4444',
          dark: '#991b1b',
        },
        warning: {
          DEFAULT: '#d97706', // Muted amber
          light: '#f59e0b',
          dark: '#92400e',
        },
      },
    },
  },
  plugins: [],
}
