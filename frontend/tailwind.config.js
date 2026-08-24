/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        lams: {
          primary: "#002046",       // Deep Navy
          secondary: "#1261A3",     // Administrative Blue
          background: "#F8F9FF",    // Slate Tint Background
          surface: "#FFFFFF",       // Clean White Surface
          accent: "#0056B3",        // Accent Blue
          border: "#E2E8F0",        // Light Gray Border
          dark: "#0F172A",          // Dark Text
          muted: "#64748B",         // Muted Text
          success: "#059669",       // Green Status
          warning: "#D97706",       // Yellow/Orange Status
          danger: "#DC2626",        // Red Status
          info: "#2563EB",          // Info Status
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgba(0, 32, 70, 0.08), 0 1px 2px 0 rgba(0, 32, 70, 0.04)',
        'card-hover': '0 4px 12px 0 rgba(0, 32, 70, 0.12), 0 2px 4px 0 rgba(0, 32, 70, 0.06)',
      }
    },
  },
  plugins: [],
}

