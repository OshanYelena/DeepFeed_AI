/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-manrope)", "system-ui", "sans-serif"],
        serif: ["var(--font-literata)", "Georgia", "serif"],
        mono: ["var(--font-jetbrains)", "Menlo", "monospace"],
      },
      colors: {
        brand: {
          50: "#f0f9ff",
          100: "#e0f2fe",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
          900: "#0c4a6e",
        },
        // Design-system palette lifted from the DeepFeed Web App mockup.
        surface: {
          DEFAULT: "#0a0c1a",
          card: "#12152a",
          panel: "#0d1020",
          hover: "#1c2040",
          border: "#334155",
        },
        ink: {
          DEFAULT: "#f4f5fa",
          muted: "#9aa0b8",
          dim: "#8b90a8",
          faint: "#5d6280",
          soft: "#7c8199",
          body: "#c3c7d9",
          para: "#e2e4ee",
        },
        accent: {
          purple: "#7c5cf6",
          purpleSoft: "#c9bdff",
          purpleText: "#b9a6ff",
          pink: "#d946ef",
          blue: "#3b82f6",
          yellow: "#eab308",
          green: "#10b981",
          rose: "#fda4af",
        },
      },
      backgroundImage: {
        "brand-gradient": "linear-gradient(135deg, #d946ef, #7c5cf6)",
        "brand-gradient-h": "linear-gradient(90deg, #3b82f6, #d946ef)",
        "rail-gradient": "linear-gradient(180deg, #d946ef, #7c5cf6, #3b82f6)",
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-in-out",
        "slide-up": "slideUp 0.3s ease-out",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        fadeIn: { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        slideUp: { "0%": { transform: "translateY(8px)", opacity: "0" }, "100%": { transform: "translateY(0)", opacity: "1" } },
      },
    },
  },
  plugins: [],
};
