/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1D4ED8',
        },
        surface: {
          canvas: '#F8FAFC',
          card: '#FFFFFF',
          elevated: '#F1F5F9',
          sidebar: '#0F172A',
          sidebarHover: '#1E293B',
        },
        risk: {
          low: '#059669',
          lowBg: '#ECFDF5',
          lowBorder: '#A7F3D0',
          medium: '#D97706',
          mediumBg: '#FFFBEB',
          mediumBorder: '#FDE68A',
          high: '#DC2626',
          highBg: '#FEF2F2',
          highBorder: '#FECACA',
          critical: '#7C3AED',
          criticalBg: '#F5F3FF',
          criticalBorder: '#DDD6FE',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      }
    },
  },
  plugins: [],
}
