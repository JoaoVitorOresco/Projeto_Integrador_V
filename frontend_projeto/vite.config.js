// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, 
    port: 5173, 
    hmr: {
    },
    watch: {
    },
    allowedHosts: [
      'esgrimetrics.ngrok.app'
    ],
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:x', //URL servidor django
        changeOrigin: true,
      }
    },
  },
})