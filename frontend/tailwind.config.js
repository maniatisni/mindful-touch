/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./ui/index.html",
    "./ui/main.js",
    "./ui/*.{html,js}"
  ],
  theme: {
    extend: {
      backdropBlur: {
        '20': '20px',
      },
      colors: {
        glass: {
          50: 'rgba(255, 255, 255, 0.9)',
          100: 'rgba(255, 255, 255, 0.8)',
          200: 'rgba(255, 255, 255, 0.7)',
          300: 'rgba(255, 255, 255, 0.6)',
          400: 'rgba(255, 255, 255, 0.5)',
          500: 'rgba(255, 255, 255, 0.4)',
          600: 'rgba(255, 255, 255, 0.3)',
          700: 'rgba(255, 255, 255, 0.2)',
          800: 'rgba(255, 255, 255, 0.1)',
          900: 'rgba(255, 255, 255, 0.05)',
        }
      }
    },
  },
  plugins: [],
}