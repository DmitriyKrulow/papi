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
    
    // Если Network Error (сервер не отвечает) - НЕ удаляем токен!
    if (!error.response) {
      return Promise.reject(error);
    }
    
    // Если 401 - токен истек или невалидный
    if (error.response?.status === 401 && !originalRequest?._retried) {
      if (isLoggingOut) {
        return Promise.reject(error);
      }
      
      isLoggingOut = true;
      
      try {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
          window.location.href = '/login';
        }
      } finally {
        isLoggingOut = false;
      }
      
      return Promise.reject(error);
    }
    
    return Promise.reject(error);
  }
);

export const API_BASE = '/api';

export const apiClient = {
  // Аутентификация
  auth: {
    login: (data: { username: string; password: string }) => 
      api.post('/auth/login', data),
    register: (data: { username: string; password: string; email: string; full_name?: string; phone?: string }) => 
      api.post('/auth/register', data),
    me: () => api.get('/auth/me'),
    profile: (data: { username?: string; email?: string; full_name?: string; phone?: string }) => 
      api.put('/auth/profile', data),
    changePassword: (data: { old_password: string; new_password: string }) => 
      api.post('/auth/change-password', data),
  },
  
  // База данных
  checkDB: () => api.get('/db-check'),
  
  // Активы
  assets: {
    list: () => api.get('/assets/'),
    get: (id: number) => api.get(`/assets/${id}/`),
    create: (data: Record<string, unknown>) => api.post('/assets/', data),
    update: (id: number, data: Record<string, unknown>) => api.put(`/assets/${id}/`, data),
    hide: (id: number) => api.put(`/assets/${id}/hide/`),
    delete: (id: number) => api.delete(`/assets/${id}/`),
  },
  
  // Документы/Файлы
  documents: {
    list: () => api.get('/documents'),
    get: (id: number) => api.get(`/documents/${id}`),
    upload: (file: File, data?: Record<string, unknown>) => {
      const formData = new FormData();
      formData.append('file', file);
      if (data) {
        Object.entries(data).forEach(([key, value]) => {
          formData.append(key, String(value));
        });
      }
      return api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    delete: (id: number) => api.delete(`/documents/${id}`),
  },
  
  // Фотографии активов
  assetPhotos: {
    upload: (assetId: number, file: File, data?: Record<string, unknown>) => {
      const formData = new FormData();
      formData.append('file', file);
      if (data) {
        Object.entries(data).forEach(([key, value]) => {
          formData.append(key, String(value));
        });
      }
      return api.post(`/asset-photos/${assetId}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    list: (assetId: number) => api.get(`/assets/${assetId}/photos`),
    get: (photoId: number) => api.get(`/asset-photos/${photoId}`),
    delete: (photoId: number) => api.delete(`/asset-photos/${photoId}`),
  },
  
  // Размещения (подразделения)
  placements: {
    list: (params?: Record<string, unknown>) => {
      const query = new URLSearchParams(params as unknown as string[]).toString();
      return api.get(`/admin/placements/?${query}`);
    },
    get: (id: number) => api.get(`/admin/placements/${id}/`),
    create: (data: Record<string, unknown>) => api.post('/admin/placements/', data),
    update: (id: number, data: Record<string, unknown>) => api.put(`/admin/placements/${id}/`, data),
    delete: (id: number) => api.delete(`/admin/placements/${id}/`),
    options: () => api.get('/admin/placements/options'),
    getEmployees: (id: number) => api.get(`/admin/placements/${id}/employees`),
    getTree: () => api.get('/admin/placements/tree'),
    getRooms: (departmentId: number) => api.get(`/admin/placements/${departmentId}/rooms`),
    createRoom: (departmentId: number, data: Record<string, unknown>) => api.post(`/admin/placements/${departmentId}/rooms`, data),
    updateRoom: (roomId: number, data: Record<string, unknown>) => api.put(`/admin/placements/rooms/${roomId}`, data),
    deleteRoom: (roomId: number) => api.delete(`/admin/placements/rooms/${roomId}`),
    moveRoom: (roomId: number, data: Record<string, unknown>) => api.put(`/admin/placements/rooms/${roomId}/move`, data),
  },
  
  // Сотрудники
  employees: {
    list: (params?: Record<string, unknown>) => {
      const query = new URLSearchParams(params as unknown as string[]).toString();
      return api.get(`/admin/employees/?${query}`);
    },
    get: (id: number) => api.get(`/admin/employees/${id}/`),
    create: (data: Record<string, unknown>) => api.post('/admin/employees/', data),
    update: (id: number, data: Record<string, unknown>) => api.put(`/admin/employees/${id}/`, data),
    delete: (id: number) => api.delete(`/admin/employees/${id}/`),
    options: () => api.get('/admin/employees/options'),
  },
  
  // Размещение активов
  placementAssignments: {
    list: (params?: Record<string, unknown>) => {
      const query = new URLSearchParams(params as unknown as string[]).toString();
      return api.get(`/admin/placement-assignments/?${query}`);
    },
    create: (data: Record<string, unknown>) => api.post('/admin/placement-assignments/', data),
    update: (id: number, data: Record<string, unknown>) => api.put(`/admin/placement-assignments/${id}/`, data),
    delete: (id: number) => api.delete(`/admin/placement-assignments/${id}/`),
    departments: (params?: Record<string, unknown>) => {
      const query = new URLSearchParams(params as unknown as string[]).toString();
      return api.get(`/admin/placement-assignments/departments?${query}`);
    },
    employees: (params?: Record<string, unknown>) => {
      const query = new URLSearchParams(params as unknown as string[]).toString();
      return api.get(`/admin/placement-assignments/employees?${query}`);
    },
  },
  
  // Ремонты
  repairs: {
    list: () => api.get('/repairs/'),
    get: (id: number) => api.get(`/repairs/${id}/`),
    create: (data: Record<string, unknown>) => api.post('/repairs/', data),
    update: (id: number, data: Record<string, unknown>) => api.put(`/repairs/${id}/`, data),
    updateStatus: (id: number, status: string) => 
      api.patch(`/repairs/${id}/status/`, { status_update: { status } }),
    updatePriority: (id: number, priority: string) => 
      api.patch(`/repairs/${id}/priority/`, { priority }),
    delete: (id: number) => api.delete(`/repairs/${id}/`),
  },
};

export default api;
