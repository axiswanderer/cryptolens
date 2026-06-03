import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./app/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg:      "#020304",
        bg1:     "#05080a",
        bg2:     "#080d10",
        bg3:     "#0c1318",
        bg4:     "#101a20",
        green:   "#00ff8c",
        green2:  "#00cc6a",
        amber:   "#ffaa00",
        red:     "#ff2d55",
        cyan:    "#00e5ff",
        muted:   "#4a7a5e",
        dim:     "#243330",
      },
      fontFamily: {
        display: ["Orbitron", "monospace"],
        mono:    ["Share Tech Mono", "monospace"],
        body:    ["Space Mono", "monospace"],
      },
      borderColor: {
        DEFAULT: "rgba(0,255,140,0.12)",
        bright:  "rgba(0,255,140,0.22)",
      },
    },
  },
  plugins: [],
};
export default config;
