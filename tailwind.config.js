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
  daisyui: {
    themes: [
      {
        light: {
          "primary": "#ecc206",
          "primary-content": "#000000",
          "secondary": "#9333ea",
          "secondary-content": "#ffffff",
          "accent": "#10b981",
          "accent-content": "#ffffff",
          "neutral": "#1f2937",
          "neutral-content": "#ffffff",
          "base-100": "#ffffff",
          "base-200": "#f3f4f6",
          "base-300": "#d1d5db",
          "base-content": "#111827",
          "info": "#3b82f6",
          "info-content": "#ffffff",
          "success": "#10b981",
          "success-content": "#ffffff",
          "warning": "#f59e0b",
          "warning-content": "#000000",
          "error": "#ef4444",
          "error-content": "#ffffff",
        },
      },
    ],
  },
}