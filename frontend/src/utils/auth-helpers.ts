// frontend/src/utils/auth-helpers.ts
import toast from 'react-hot-toast';

let isLoggingOut = false;
let tokenExpiredToastShown = false;

/**
 * Очищает сессию и перенаправляет на страницу входа
 * Вызывается при истечении токена
 */
export function handleTokenExpired() {
  if (isLoggingOut) return;
  isLoggingOut = true;
  
  // Очищаем данные сессии
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  
  // Показываем уведомление только один раз
  if (!tokenExpiredToastShown) {
    tokenExpiredToastShown = true;
    toast.error('Сеанс истек. Пожалуйста, войдите снова.', {
      duration: 5000,
      icon: '🔑',
    });
    
    // Сбрасываем флаг через 5 секунд чтобы показать снова при необходимости
    setTimeout(() => {
      tokenExpiredToastShown = false;
    }, 5000);
  }
  
  // Если пользователь не на странице логина/регистрации - редиректим
  if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
    window.location.href = '/login';
  }
  
  isLoggingOut = false;
}

/**
 * Обертка над fetch с обработкой 401 ошибок
 */
export async function authenticatedFetch(url: string, options: RequestInit = {}): Promise<Response | null> {
  const token = localStorage.getItem('token');
  
  // Добавляем токен к заголовкам если есть
  const headers = {
    ...(options.headers as Record<string, string> || {}),
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  };
  
  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });
    
    // Если 401 - токен истек
    if (response.status === 401) {
      handleTokenExpired();
      return null;
    }
    
    return response;
  } catch (error) {
    console.error('Fetch error:', error);
    return null;
  }
}

/**
 * Проверяет текущий токен и перенаправляет если он истек
 * Используется для инициализации при загрузке страницы
 */
export async function checkAndRefreshSession(): Promise<boolean> {
  const token = localStorage.getItem('token');
  if (!token) return false;
  
  try {
    const response = await fetch('/api/auth/me', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    if (response.status === 401) {
      handleTokenExpired();
      return false;
    }
    
    return response.ok;
  } catch (error) {
    console.error('Session check error:', error);
    return false;
  }
}
