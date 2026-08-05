// frontend/src/utils/global-fetch-handler.ts
// Глобальная обертка fetch для обработки истечения токена
import { handleTokenExpired } from './auth-helpers';

const originalFetch = window.fetch;

window.fetch = async function (...args: Parameters<typeof fetch>): Promise<Response> {
  const [url, options] = args;
  
  // Преобразуем URL в строку для проверки
  const urlString = typeof url === 'string' ? url : url instanceof URL ? url.href : '';
  
  // Пропускаем проверку для публичных endpoints
  const publicUrls = [
    '/api/auth/login',
    '/api/auth/register',
    '/api/password-reset/',
  ];
  
  const isPublic = publicUrls.some(publicUrl => urlString.includes(publicUrl));
  
  if (!isPublic && urlString.startsWith('/api/')) {
    try {
      const response = await originalFetch.apply(window, args);
      
      // Если 401 - токен истек
      if (response.status === 401) {
        handleTokenExpired();
        // Возвращаем "пустой" ответ чтобы не ломать код
        return new Response(null, {
          status: response.status,
          statusText: response.statusText,
        });
      }
      
      return response;
    } catch (error) {
      console.error('Global fetch error:', error);
      throw error;
    }
  }
  
  return originalFetch.apply(window, args);
};

// Обертка для XMLHttpRequest
const originalXHROpen = XMLHttpRequest.prototype.open;
const originalXHRSend = XMLHttpRequest.prototype.send;

(XMLHttpRequest.prototype as any).open = function(this: any, method: string, url: string | URL, ...rest: any[]) {
  this._requestUrl = String(url);
  return (originalXHROpen as any).apply(this, [method, url, ...rest]);
};

(XMLHttpRequest.prototype as any).send = function(this: any, body?: any) {
  const xhr = this;
  const originalOnReadyStateChange = xhr.onreadystatechange;
  
  xhr.onreadystatechange = function() {
    if (xhr.readyState === 4) {
      const url = xhr._requestUrl || '';
      
      // Если 401 - токен истек
      if (xhr.status === 401 && !url.includes('/auth/login') && !url.includes('/auth/register')) {
        handleTokenExpired();
      }
    }
    
    if (originalOnReadyStateChange) {
      originalOnReadyStateChange.apply(this, []);
    }
  };
  
  return originalXHRSend.apply(this, [body]);
};

export {};
