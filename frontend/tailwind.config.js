/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // ── Wakili brand palette ─────────────────────────────────────
        primary:    "#977dff",   // violet – main actions, CTAs
        accent:     "#02effe",   // cyan   – highlights, active states
        highlight:  "#ffccf2",   // pink   – risk flags, notifications
        bg: {
          main:      "#f2e6ee",  // lavender blush – page background
          card:      "#ffffff",  // white cards
          panel:     "#aee1f9",  // sky blue – secondary panels
          analytics: "#9ac5fc",  // cornflower – analytics widgets
        },
        // Semantic aliases
        risk: {
          high:   "#ef4444",
          medium: "#f97316",
          low:    "#22c55e",
        },
      },
      fontFamily: {
        // Distinctive pairing: display + body
        display: ["'Playfair Display'", "Georgia", "serif"],
        body:    ["'DM Sans'", "system-ui", "sans-serif"],
        mono:    ["'JetBrains Mono'", "monospace"],
      },
      borderRadius: {
        xl2: "1.25rem",
        xl3: "1.75rem",
      },
      boxShadow: {
        card:  "0 4px 24px 0 rgba(151,125,255,0.10)",
        float: "0 8px 40px 0 rgba(151,125,255,0.18)",
      },
      animation: {
        "fade-in":     "fadeIn 0.4s ease both",
        "slide-up":    "slideUp 0.4s ease both",
        "pulse-slow":  "pulse 3s ease-in-out infinite",
      },
      keyframes: {
        fadeIn:  { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp: { from: { opacity: 0, transform: "translateY(16px)" }, to: { opacity: 1, transform: "translateY(0)" } },
      },
    },
  },
  plugins: [],
};
