/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#FAFAF8",
        ink: "#201F1D",
        moss: "#3F6B4F",
        brick: "#9C4A3A",
        amber: "#B98A2E",
        slate: "#6B6862",
        line: "#E4E1D9",
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
