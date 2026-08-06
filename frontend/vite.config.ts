// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  
  // === НАСТРОЙКИ ДЛЯ РАЗРАБОТКИ (npm run dev) ===
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
      '/docs': {
        target: 'http://localhost:8888',
        changeOrigin: true,
        secure: false,
      },
      '/openapi.json': {
        target: 'http://localhost:8888',
        changeOrigin: true,
        secure: false,
      },
      '/oauth2-redirect': {
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

  // === НАСТРОЙКИ ДЛЯ ПРОДАКШЕНА (npm run build) ===
  build: {
    // Увеличиваем лимит предупреждения о размере чанков
    chunkSizeWarningLimit: 1000,
    
    // Настройки сборки
    rollupOptions: {
      output: {
        // Ручное разделение кода на чанки
        manualChunks(id) {
          // Все библиотеки из node_modules
          if (id.includes('node_modules')) {
            // React и его экосистема
            if (id.includes('react') || id.includes('react-dom') || id.includes('react-router-dom')) {
              return 'react-vendor'
            }
            // UI-библиотеки (формы, иконки)
            if (id.includes('@hookform') || id.includes('lucide-react')) {
              return 'ui-vendor'
            }
            // Дата-библиотеки
            if (id.includes('date-fns')) {
              return 'date-vendor'
            }
            // API-клиенты
            if (id.includes('axios')) {
              return 'api-vendor'
            }
            // Все остальные библиотеки
            return 'vendor'
          }
          // Код приложения остаётся в основном чанке
          return undefined
        },
        
        // Оптимизация имен файлов для кеширования
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
      },
    },
    
    // Дополнительные настройки для уменьшения размера
    minify: 'esbuild', // или 'terser' для более агрессивной минификации
    sourcemap: false,  // Отключаем sourcemap в продакшене
    target: 'es2015',  // Поддержка старых браузеров
  },
  
  // === ОПЦИОНАЛЬНО: Настройки для Nginx (для информации) ===
  // При сборке статика кладётся в /opt/papi/frontend/dist
  // Nginx должен быть настроен на раздачу этой папки
})