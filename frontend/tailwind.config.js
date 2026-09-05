/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        glass: {
          base: "rgba(15, 23, 42, 0.75)",
          surface: "rgba(30, 41, 59, 0.65)",
          border: "rgba(255, 255, 255, 0.12)",
          highlight: "rgba(255, 255, 255, 0.05)",
          ai: "rgba(99, 102, 241, 0.15)",
        },
        neo: {
          bg: "#0B0F19",
          card: "#131B2E",
          border: "#1E293B",
          accent: "#38BDF8",
          primary: "#6366F1",
          success: "#10B981",
          warning: "#F59E0B",
          danger: "#EF4444",
          purple: "#8B5CF6",
        }
      },
      boxShadow: {
        'neo-sm': '2px 2px 0px rgba(0, 0, 0, 0.6)',
        'neo': '4px 4px 0px rgba(0, 0, 0, 0.8)',
        'neo-lg': '6px 6px 0px rgba(0, 0, 0, 0.9)',
        'neo-indigo': '4px 4px 0px rgba(99, 102, 241, 0.6)',
        'neo-rose': '4px 4px 0px rgba(239, 68, 68, 0.6)',
        'neo-emerald': '4px 4px 0px rgba(16, 185, 129, 0.6)',
        'glass-glow': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        'ai-glow': '0 0 25px 0 rgba(99, 102, 241, 0.3)',
      },
      backdropBlur: {
        'glass': '16px',
        'glass-lg': '24px',
      }
    },
  },
  plugins: [],
}
