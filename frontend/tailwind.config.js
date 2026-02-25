/** @type {import('tailwindcss').Config} */
export default {
    content: ['./index.html', './src/**/*.{js,jsx}'],
    theme: {
        extend: {
            colors: {
                brand: {
                    50: '#eef2ff',
                    100: '#e0e7ff',
                    500: '#6366f1',
                    600: '#4f46e5',
                    700: '#4338ca',
                    900: '#1e1b4b',
                },
                risk: {
                    high: '#22c55e',
                    medium: '#f59e0b',
                    low: '#ef4444',
                },
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
