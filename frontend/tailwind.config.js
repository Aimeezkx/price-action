/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Add custom spacing for indentation
      spacing: {
        '16': '4rem',
        '20': '5rem',
        '24': '6rem',
      }
    },
  },
  plugins: [],
}