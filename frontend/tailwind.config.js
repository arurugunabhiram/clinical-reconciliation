import colors from "tailwindcss/colors";

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Remap gray → slate for the cool-grey medical theme.
        // Every existing `gray-X` Tailwind class now resolves to the slate palette.
        gray: colors.slate,
      },
    },
  },
  plugins: [],
};
