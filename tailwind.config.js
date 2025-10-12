/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './iwashcars/**/*.html',
    './iwashcars/**/*.js',
    './static/**/*.js',
    './main/templates/**/*.html',
  ],
  theme: {
    extend: {},
  },
  plugins: [require('daisyui')],
  daisyui: {
    themes: [
      {
        light: {
          ...require("daisyui/src/theming/themes")["light"],
          "primary": "#D4AF37",        // Gold color
          "primary-focus": "#B8941F",  // Darker gold for hover
          "primary-content": "#ffffff", // White text on gold buttons
        },
      },
    ],
  },
}