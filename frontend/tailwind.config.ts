import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      /* ───── Color Palette ───── */
      colors: {
        /* Primary accent — muted sage green */
        sage: {
          50: "#EAF0E8",
          100: "#D5E1D1",
          200: "#B0C9A8",
          300: "#8AB27E",
          400: "#6A9A5C",
          500: "#4D6B44",
          600: "#3E5637",
          700: "#2F412A",
          800: "#1F2C1C",
          900: "#10160E",
        },
        /* Secondary accent — dusty rose */
        rose: {
          50: "#FDF5F3",
          100: "#F5E0DB",
          200: "#E8C5C0",
          300: "#D9A49C",
          400: "#CC8A80",
          500: "#BF7068",
          600: "#A25850",
          700: "#7D4038",
        },
        /* Warm neutrals */
        warm: {
          50: "#F5F4F0",
          100: "#F0EFEB",
          200: "#E8E6E0",
          300: "#D4D2CC",
          400: "#A8A6A0",
          500: "#6B6B68",
          600: "#4A4A48",
          700: "#2E2E2C",
          800: "#1C1C1A",
          900: "#0E0E0D",
        },
        /* Semantic colors */
        success: {
          50: "#F0FDF4",
          100: "#D5E1D1",
          500: "#4D6B44",
          700: "#2F412A",
        },
        warning: {
          50: "#FFF8F1",
          100: "#FCE8D3",
          500: "#E8A87C",
          700: "#B87D52",
        },
        danger: {
          50: "#FEF2F1",
          100: "#FCCFCC",
          500: "#C0392B",
          700: "#8B2722",
        },
        info: {
          50: "#EFF6FF",
          100: "#DBEAFE",
          500: "#3B82F6",
          700: "#1D4ED8",
        },
        /* Surface tokens */
        surface: "#FFFFFF",
        "surface-alt": "#F5F4F0",
        "card-border": "#E8E6E0",
        "sidebar-active": "#EAF0E8",
      },

      /* ───── Typography ───── */
      fontFamily: {
        sans: ["var(--font-dm-sans)", "system-ui", "sans-serif"],
        display: ["var(--font-playfair)", "Georgia", "serif"],
        mono: ["var(--font-jetbrains)", "Menlo", "monospace"],
      },

      /* ───── Border Radius ───── */
      borderRadius: {
        "2xl": "16px",
        "3xl": "20px",
        "4xl": "24px",
      },

      /* ───── Shadows — soft depth, no harsh borders ───── */
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,0.06)",
        "card-hover": "0 4px 12px rgba(0,0,0,0.08)",
        "card-lg": "0 8px 24px rgba(0,0,0,0.08)",
        sidebar: "1px 0 3px rgba(0,0,0,0.04)",
        modal: "0 16px 48px rgba(0,0,0,0.12)",
        dropdown: "0 4px 16px rgba(0,0,0,0.1)",
      },

      /* ───── Animations ───── */
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        "pulse-soft": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.6" },
        },
      },
      animation: {
        shimmer: "shimmer 2s ease-in-out infinite",
        "fade-in": "fade-in 0.3s ease-out",
        "slide-up": "slide-up 0.3s ease-out",
        "scale-in": "scale-in 0.2s ease-out",
        "pulse-soft": "pulse-soft 2s ease-in-out infinite",
      },

      /* ───── Spacing ───── */
      spacing: {
        "sidebar": "256px",
        "sidebar-collapsed": "72px",
        "topbar": "64px",
      },

      /* ───── Transitions ───── */
      transitionDuration: {
        "150": "150ms",
        "200": "200ms",
        "300": "300ms",
      },
    },
  },
  plugins: [],
};

export default config;
