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
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

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

// API-методы
export const apiClient = {
  // Аутентификация
  auth: {
    login: (data: any) => api.post('/auth/login', data),
    register: (data: any) => api.post('/auth/register', data),
    me: () => api.get('/auth/me'),
    profile: (data: any) => api.put('/auth/profile', data),
    changePassword: (data: any) => api.post('/auth/change-password', data),
  },
  
  // База данных
  checkDB: () => api.get('/db-check'),
  
  // Активы
  assets: {
    list: () => api.get('/assets'),
    get: (id: number) => api.get(`/assets/${id}`),
    create: (data: any) => api.post('/assets', data),
    update: (id: number, data: any) => api.put(`/assets/${id}`, data),
    hide: (id: number) => api.put(`/assets/${id}/hide`),
    delete: (id: number) => api.delete(`/assets/${id}`),
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
};

export default api;
