// frontend/src/api/client.ts
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

// Создаем экземпляр axios с базовыми настройками
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Флаг чтобы избежать рекурсии при logout
let isLoggingOut = false;

// Перехватчик для добавления токена
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Перехватчик для обработки ошибок авторизации
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retried?: boolean };
    
    // Если 401 - токен истек или невалидный
    if (error.response?.status === 401 && !originalRequest?._retried) {
      // Не пытаемся перезапросить если уже logout
      if (isLoggingOut) {
        return Promise.reject(error);
      }
      
      isLoggingOut = true;
      
      try {
        // Очищаем данные сессии
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        // Если пользователь не на странице логина - редиректим
        if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
          window.location.href = '/login';
        }
      } finally {
        isLoggingOut = false;
      }
      
      return Promise.reject(error);
    }
    
    // Если 403 - нет прав доступа
    if (error.response?.status === 403) {
      // Пытаемся перезапросить с обновленным токеном (если это не первый запрос)
      if (originalRequest && !originalRequest._retried) {
        originalRequest._retried = true;
        const token = localStorage.getItem('token');
        if (token) {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        }
      }
    }
    
    return Promise.reject(error);
  }
);

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
  checkDB: () => api.get('/db-check'),
  
  // Активы
  assets: {
    list: () => api.get('/assets/'),
    get: (id: number) => api.get(`/assets/${id}/`),
    create: (data: any) => api.post('/assets/', data),
    update: (id: number, data: any) => api.put(`/assets/${id}/`, data),
    hide: (id: number) => api.put(`/assets/${id}/hide/`),
    delete: (id: number) => api.delete(`/assets/${id}/`),
  },
  
  // Документы/Файлы
  documents: {
    list: () => api.get('/documents'),
    get: (id: number) => api.get(`/documents/${id}`),
    upload: (file: File, data?: any) => {
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
    delete: (id: number) => api.delete(`/documents/${id}`),
  },
  
  // Фотографии активов
  assetPhotos: {
    upload: (assetId: number, file: File, data?: any) => {
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
    list: (assetId: number) => api.get(`/asset-photos/${assetId}/photos`),
    get: (photoId: number) => api.get(`/asset-photos/${photoId}`),
    delete: (photoId: number) => api.delete(`/asset-photos/${photoId}`),
  },
  
  // Размещения (подразделения)
  placements: {
    list: (params?: Record<string, any>) => {
      const query = new URLSearchParams(params as any).toString();
      return api.get(`/admin/placements/?${query}`);
    },
    get: (id: number) => api.get(`/admin/placements/${id}/`),
    create: (data: any) => api.post('/admin/placements/', data),
    update: (id: number, data: any) => api.put(`/admin/placements/${id}/`, data),
    delete: (id: number) => api.delete(`/admin/placements/${id}/`),
    options: () => api.get('/admin/placements/options'),
    getEmployees: (id: number) => api.get(`/admin/placements/${id}/employees`),
  },
  
  // Сотрудники
  employees: {
    list: (params?: Record<string, any>) => {
      const query = new URLSearchParams(params as any).toString();
      return api.get(`/admin/employees/?${query}`);
    },
    get: (id: number) => api.get(`/admin/employees/${id}/`),
    create: (data: any) => api.post('/admin/employees/', data),
    update: (id: number, data: any) => api.put(`/admin/employees/${id}/`, data),
    delete: (id: number) => api.delete(`/admin/employees/${id}/`),
    options: () => api.get('/admin/employees/options'),
  },
  
  // Размещение активов
  placementAssignments: {
    list: (params?: Record<string, any>) => {
      const query = new URLSearchParams(params as any).toString();
      return api.get(`/admin/placement-assignments/?${query}`);
    },
    create: (data: any) => api.post('/admin/placement-assignments/', data),
    update: (id: number, data: any) => api.put(`/admin/placement-assignments/${id}/`, data),
    delete: (id: number) => api.delete(`/admin/placement-assignments/${id}/`),
    departments: (params?: Record<string, any>) => {
      const query = new URLSearchParams(params as any).toString();
      return api.get(`/admin/placement-assignments/departments?${query}`);
    },
    employees: (params?: Record<string, any>) => {
      const query = new URLSearchParams(params as any).toString();
      return api.get(`/admin/placement-assignments/employees?${query}`);
    },
  },
  
  // Ремонты
  repairs: {
    list: () => {
      console.log('[API Client] repairs.list called');
      return api.get('/repairs/');
    },
    get: (id: number) => {
      console.log('[API Client] repairs.get called with id:', id);
      return api.get(`/repairs/${id}/`);
    },
    create: (data: any) => {
      console.log('[API Client] repairs.create called');
      return api.post('/repairs/', data);
    },
    update: (id: number, data: any) => {
      console.log('[API Client] repairs.update called with id:', id);
      return api.put(`/repairs/${id}/`, data);
    },
    updateStatus: (id: number, status: string) => {
      console.log('[API Client] repairs.updateStatus called with id:', id, 'status:', status);
      const token = localStorage.getItem('token');
      console.log('[API Client] Token from localStorage:', token ? token.substring(0, 30) + '...' : 'NONE');
      console.log('[API Client] Token type:', typeof token);
      console.log('[API Client] Token length:', token?.length);
      console.log('[API Client] Token first 100 chars:', token?.substring(0, 100));
      const result = api.patch(`/repairs/${id}/status/`, { status_update: { status } });
      console.log('[API Client] PATCH result:', result);
      return result;
    },
    updatePriority: (id: number, priority: string) => {
      console.log('[API Client] repairs.updatePriority called with id:', id, 'priority:', priority);
      return api.patch(`/repairs/${id}/priority/`, { priority });
    },
    delete: (id: number) => {
      console.log('[API Client] repairs.delete called with id:', id);
      return api.delete(`/repairs/${id}/`);
    },
  },
};

export default api;
