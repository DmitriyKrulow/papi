// frontend/src/api/client.ts
import axios from 'axios';

// Создаем экземпляр axios с базовыми настройками
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Перехватчик для добавления токена
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    console.log('[Interceptor] BEFORE: Token from localStorage:', token ? token.substring(0, 30) + '...' : 'NONE');
    console.log('[Interceptor] BEFORE: config.headers:', config.headers);
    console.log('[Interceptor] BEFORE: Authorization header?', config.headers.Authorization ? 'EXISTS' : 'MISSING');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('[Interceptor] ✅ Set Authorization header:', token.substring(0, 30) + '...');
    } else {
      console.error('[Interceptor] ❌ NO TOKEN - This is the problem!');
      console.error('[Interceptor] ❌ localStorage keys:', Object.keys(localStorage));
    }
    console.log('[Interceptor] AFTER: config.headers after modification:', config.headers);
    console.log('[Interceptor] AFTER: Authorization header?', config.headers.Authorization ? 'EXISTS' : 'MISSING');
    return config;
  },
  (error) => {
    console.error('[Interceptor] Error:', error);
    return Promise.reject(error);
  }
);

// Перехватчик для обработки ошибок
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Проверка токена перед каждым запросом
const checkToken = () => {
  const token = localStorage.getItem('token');
  console.log('[Client Check] Token exists:', !!token);
  if (!token) {
    console.error('[Client Check] ❌ NO TOKEN IN LOCALSTORAGE!');
    console.error('[Client Check] localStorage contents:', {
      keys: Object.keys(localStorage),
      user: localStorage.getItem('user'),
    });
  } else {
    console.log('[Client Check] ✅ Token found:', token.substring(0, 30) + '...');
  }
  return token;
};

// API-методы
export const apiClient = {
  // Аутентификация
  auth: {
    login: (data: any) => {
      console.log('[Auth API] login called');
      return api.post('/auth/login', data);
    },
    register: (data: any) => {
      console.log('[Auth API] register called');
      return api.post('/auth/register', data);
    },
    me: () => {
      console.log('[Auth API] me called');
      return api.get('/auth/me');
    },
    profile: (data: any) => {
      console.log('[Auth API] profile called');
      return api.put('/auth/profile', data);
    },
    changePassword: (data: any) => {
      console.log('[Auth API] changePassword called');
      return api.post('/auth/change-password', data);
    },
  },
  
  // База данных
  checkDB: () => {
    checkToken();
    return api.get('/db-check');
  },
  
  // Активы
  assets: {
    list: () => {
      checkToken();
      return api.get('/assets/');
    },
    get: (id: number) => {
      checkToken();
      return api.get(`/assets/${id}/`);
    },
    create: (data: any) => {
      checkToken();
      return api.post('/assets/', data);
    },
    update: (id: number, data: any) => {
      checkToken();
      return api.put(`/assets/${id}/`, data);
    },
    hide: (id: number) => {
      checkToken();
      return api.put(`/assets/${id}/hide/`);
    },
    delete: (id: number) => {
      checkToken();
      return api.delete(`/assets/${id}/`);
    },
  },
  
  // Документы/Файлы
  documents: {
    list: () => {
      checkToken();
      return api.get('/documents');
    },
    get: (id: number) => {
      checkToken();
      return api.get(`/documents/${id}`);
    },
    upload: (file: File, data?: any) => {
      checkToken();
      const formData = new FormData();
      formData.append('file', file);
      if (data) {
        Object.entries(data).forEach(([key, value]) => {
          formData.append(key, String(value));
        });
      }
      return api.post('/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
    },
    delete: (id: number) => {
      checkToken();
      return api.delete(`/documents/${id}`);
    },
  },
  
  // Фотографии активов
  assetPhotos: {
    upload: (assetId: number, file: File, data?: any) => {
      checkToken();
      const formData = new FormData();
      formData.append('file', file);
      if (data) {
        Object.entries(data).forEach(([key, value]) => {
          formData.append(key, String(value));
        });
      }
      return api.post(`/asset-photos/${assetId}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
    },
    list: (assetId: number) => {
      checkToken();
      return api.get(`/asset-photos/${assetId}/photos`);
    },
    get: (photoId: number) => {
      checkToken();
      return api.get(`/asset-photos/${photoId}`);
    },
    delete: (photoId: number) => {
      checkToken();
      return api.delete(`/asset-photos/${photoId}`);
    },
  },
  
  // Ремонты
  repairs: {
    list: () => {
      console.log('[API Client] repairs.list called');
      checkToken();
      return api.get('/repairs/');
    },
    get: (id: number) => {
      console.log('[API Client] repairs.get called with id:', id);
      checkToken();
      return api.get(`/repairs/${id}/`);
    },
    create: (data: any) => {
      console.log('[API Client] repairs.create called');
      checkToken();
      return api.post('/repairs/', data);
    },
    update: (id: number, data: any) => {
      console.log('[API Client] repairs.update called with id:', id);
      checkToken();
      return api.put(`/repairs/${id}/`, data);
    },
    updateStatus: (id: number, status: string) => {
      console.log('[API Client] repairs.updateStatus called with id:', id, 'status:', status);
      const token = localStorage.getItem('token');
      console.log('[API Client] Token from localStorage:', token ? token.substring(0, 30) + '...' : 'NONE');
      console.log('[API Client] Token type:', typeof token);
      console.log('[API Client] Token length:', token?.length);
      console.log('[API Client] Token first 100 chars:', token?.substring(0, 100));
      checkToken();
      const result = api.patch(`/repairs/${id}/status/`, { status_update: { status } });
      console.log('[API Client] PATCH result:', result);
      return result;
    },
    updatePriority: (id: number, priority: string) => {
      console.log('[API Client] repairs.updatePriority called with id:', id, 'priority:', priority);
      checkToken();
      return api.patch(`/repairs/${id}/priority/`, { priority });
    },
    delete: (id: number) => {
      console.log('[API Client] repairs.delete called with id:', id);
      checkToken();
      return api.delete(`/repairs/${id}/`);
    },
  },
};

export default api;
