/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#0B1220",
          900: "#111827",
          800: "#1F2937",
        },
      },
    },
  },
  plugins: [],
};