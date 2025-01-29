/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js",
    "./templates/**/*.{html,js}",
    "./templates/components/**/*.{html,js}"
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}