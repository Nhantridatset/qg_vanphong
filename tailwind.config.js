/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './qg_vanphong/core/templates/**/*.html',
    './qg_vanphong/users/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#6366F1', // Indigo 500
        secondary: '#8B5CF6', // Violet 500
        accent: '#EC4899', // Pink 500
        background: '#F3F4F6', // Gray 100
        text: '#1F2937', // Gray 900
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};
