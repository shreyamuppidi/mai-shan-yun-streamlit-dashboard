import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  define: {
    'process.env': '{}',
    global: 'globalThis',
    'process.browser': 'true',
  },
  optimizeDeps: {
    include: ['plotly.js'],
    esbuildOptions: {
      define: {
        global: 'globalThis',
      },
    },
  },
  server: {
    port: 5173,
    host: true, // Listen on all addresses
    open: true, // Automatically open browser
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    commonjsOptions: {
      include: [/plotly.js/, /node_modules/],
    },
  },
})

