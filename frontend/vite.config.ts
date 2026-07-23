// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8888',  // ← Ваш порт бэкенда
        changeOrigin: true,
        secure: false,
      },
      '/docs': {
        target: 'http://localhost:8888',
        changeOrigin: true,
        secure: false,
      },
      '/static': {
        target: 'http://localhost:8888',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})