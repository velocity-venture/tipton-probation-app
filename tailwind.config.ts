import type { Config } from 'tailwindcss'

export default {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0E0E10',
        surface: '#1C1C1F',
        border: '#2E2E32',
        primary: '#5E6AD2',
        alert: '#F81CE5',
        text: {
          primary: '#EDEDEF',
          secondary: '#8B8B8D',
          muted: '#5C5C5E',
        },
        risk: {
          low: '#30A46C',
          medium: '#FFB224',
          high: '#F76808',
          warrant: '#E5484D',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [],
} satisfies Config

