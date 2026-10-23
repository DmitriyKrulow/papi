// frontend/tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Новая палитра: приглушённый сине-серый + бирюзовый акцент
        brand: {
          DEFAULT: '#4F6A8C',
          50: '#EEF2F7',
          100: '#D5DDE8',
          200: '#A8B8D0',
          300: '#7B92B8',
          400: '#5C7AA3',
          500: '#4F6A8C',
          600: '#3E5573',
          700: '#324560',
          800: '#2C3A50',
          900: '#253044',
        },
        accent: {
          DEFAULT: '#2DD4EB',
          50: '#ECFCFE',
          100: '#C9F8FB',
          200: '#93EFF7',
          300: '#5AE5F1',
          400: '#2DD4EB',
          500: '#1AB8CC',
          600: '#1493A5',
          700: '#107280',
          800: '#0D5762',
          900: '#0A434D',
        },
        // Графитовые тона для тёмной темы
        graphite: {
          50: '#F5F6F7',
          100: '#E5E7EB',
          200: '#CCCCCC',
          300: '#B3B6BA',
          400: '#999D9F',
          500: '#808488',
          600: '#666A6E',
          700: '#4D5054',
          800: '#2C323A',
          900: '#1A1F25',
          950: '#121314',
        },
        gray: {
          750: '#2d3748',
        },
      },
      borderRadius: {
        'card': '14px',
        'card-sm': '10px',
        'card-lg': '18px',
      },
      boxShadow: {
        'card': '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)',
        'card-selected': '0 0 0 2px #2DD4EB, 0 2px 8px rgba(45,212,191,0.2)',
      },
      keyframes: {
        'scan-pulse': {
          '0%, 100%': { transform: 'scale(1)', opacity: '1' },
          '50%': { transform: 'scale(1.5)', opacity: '0.5' },
        },
        'scan-wave': {
          '0%': { transform: 'scale(0.8)', opacity: '0.8' },
          '100%': { transform: 'scale(2.2)', opacity: '0' },
        },
        'slide-in-right': {
          '0%': { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        'slide-in-left': {
          '0%': { transform: 'translateX(-100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        'compact-mode': {
          '0%': { padding: '1rem' },
          '100%': { padding: '0.5rem' },
        },
      },
      animation: {
        'scan-pulse': 'scan-pulse 1.5s ease-in-out infinite',
        'scan-wave': 'scan-wave 1s ease-out forwards',
        'slide-in-right': 'slide-in-right 0.3s ease-out',
        'slide-in-left': 'slide-in-left 0.3s ease-out',
      },
    },
  },
  plugins: [],
}