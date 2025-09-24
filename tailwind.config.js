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
}