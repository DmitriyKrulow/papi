// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8888',
        changeOrigin: true,
        secure: false,
        configure: (proxy) => {
          proxy.on("proxyReq", (proxyReq, req) => {
            if (req.headers.authorization) {
              proxyReq.setHeader("Authorization", req.headers.authorization);
            }
          });
        },
      },
      "/docs": {
        target: "http://localhost:8888",
        changeOrigin: true,
        secure: false,
      },
      "/static": {
        target: "http://localhost:8888",
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
