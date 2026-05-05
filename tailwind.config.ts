import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#151515",
        paper: "#fbfaf7",
        sage: "#2f7d59",
        amber: "#a16207",
        coral: "#b42318",
      },
      boxShadow: {
        soft: "0 18px 60px rgba(20, 20, 20, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
