import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#977dff",
          dark: "#7c5dfa",
        },
        accent: "#02effe",
        background: "#f2e6ee",
        panel: "#aee1f9",
        analytics: "#9ac5fc",
        highlight: "#ffccf2",
      },
      fontFamily: {
        display: ["'Playfair Display'", "serif"],
        body: ["'DM Sans'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      backgroundImage: {
        "gradient-wakili": "linear-gradient(135deg, #977dff 0%, #02effe 100%)",
        "gradient-soft": "linear-gradient(135deg, #f2e6ee 0%, #aee1f9 100%)",
      },
      boxShadow: {
        card: "0 4px 24px rgba(151,125,255,0.08)",
        "card-lg": "0 12px 48px rgba(151,125,255,0.15)",
        glow: "0 0 20px rgba(2,239,254,0.3)",
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
    },
  },
  plugins: [],
};

export default config;