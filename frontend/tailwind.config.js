/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // DeepScribe-inspired palette
        primary: {
          DEFAULT: '#00A1F4',
          dark: '#0057A3',
        },
        hero: {
          bgStart: '#020617',
          bgEnd: '#0B1434',
        },
        surface: {
          DEFAULT: '#FFFFFF',
          alt: '#F8FAFC',
        },
        border: {
          subtle: '#E2E8F0',
        },
        text: {
          primary: '#0F172A',
          secondary: '#64748B',
        },
        badge: {
          info: '#00A1F4',
          warning: '#F97316',
          danger: '#DC2626',
        },
      },
      backgroundColor: {
        'surface': '#FFFFFF',
        'surface-alt': '#F8FAFC',
      },
      textColor: {
        'text-primary': '#0F172A',
        'text-secondary': '#64748B',
      },
      borderColor: {
        'border-subtle': '#E2E8F0',
      },
      fontFamily: {
        sans: [
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          '"SF Pro Text"',
          '"Inter"',
          'sans-serif',
        ],
      },
      borderRadius: {
        card: '24px',
      },
      boxShadow: {
        card: '0 18px 40px rgba(15, 23, 42, 0.10)',
        'card-hover': '0 24px 48px rgba(15, 23, 42, 0.15)',
      },
    },
  },
  plugins: [],
}
