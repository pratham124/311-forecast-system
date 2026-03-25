/** @type {import("tailwindcss").Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Space Grotesk', 'Avenir Next', 'Segoe UI', 'sans-serif'],
      },
      colors: {
        ink: '#193A5A',
        muted: '#4C6480',
        accent: '#005087',
        history: '#193A5A',
        forecast: '#0081BC',
      },
      boxShadow: {
        panel: '0 18px 44px rgba(0, 80, 135, 0.12)',
      },
    },
  },
  plugins: [],
};
