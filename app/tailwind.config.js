/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./App.tsx",
    "./src/**/*.{ts,tsx}",
  ],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#E6F4FE',
          100: '#B3DFFC',
          200: '#80CAFA',
          300: '#4DB5F8',
          400: '#1A9FF6',
          500: '#0880D7',
          600: '#0664A7',
          700: '#044777',
          800: '#022B47',
          900: '#000F17',
        },
        accent: {
          50: '#FFF7ED',
          100: '#FFEBD5',
          200: '#FFD7AA',
          300: '#FFC380',
          400: '#FFAF55',
          500: '#FF9B2B',
          600: '#D67A00',
          700: '#A35D00',
          800: '#704000',
          900: '#3D2300',
        },
        danger: '#EF4444',
        success: '#22C55E',
        warning: '#F59E0B',
      },
      fontFamily: {
        sans: ['System'],
        mono: ['monospace'],
      },
    },
  },
  plugins: [],
};
