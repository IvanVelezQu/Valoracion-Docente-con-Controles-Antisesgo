/** @type {import("tailwindcss").Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        udea: {
          dark: "#0d2618",
          primary: "#136538",
          nav: "#3b6e38",
          lime: "#6ea52d",
          lightlime: "#8ab532",
          gold: "#f9b218",
          graytab: "#e6e7e8",
          grayinactive: "#dcddde"
        }
      },
      fontFamily: {
        sans: ["Roboto", "Segoe UI", "sans-serif"],
        serif: ["Merriweather", "Georgia", "serif"]
      }
    }
  },
  plugins: []
};
