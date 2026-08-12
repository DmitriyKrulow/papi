// frontend/src/api/notifications.ts
import { API_BASE } from './client';

export interface NotificationItem {
  id: number;
  type: string;
  type_label: string;
  type_icon: string;
  title: string;
  message: string;
  is_read: boolean;
  reference_type?: string;
  reference_id?: number;
  entity_name?: string;
  created_at: string;
  read_at?: string;
}

export const notificationsApi = {
  list: async (params: {
    limit?: number;
    offset?: number;
    type?: string;
    unread_only?: boolean;
  } = {}) => {
    const token = localStorage.getItem('token');
    const searchParams = new URLSearchParams();
    if (params.limit) searchParams.set('limit', String(params.limit));
    if (params.offset) searchParams.set('offset', String(params.offset));
    if (params.type) searchParams.set('type', params.type);
    if (params.unread_only) searchParams.set('unread_only', 'true');

    const response = await fetch(`${API_BASE}/notifications/?${searchParams}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to fetch notifications');
    return response.json();
  },

  getUnreadCount: async () => {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE}/notifications/unread-count`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to fetch unread count');
    return response.json();
  },

  markAsRead: async (notificationId: number) => {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE}/notifications/${notificationId}/read`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to mark as read');
    return response.json();
  },

  markAllAsRead: async () => {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE}/notifications/read-all`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to mark all as read');
    return response.json();
  },

  delete: async (notificationId: number) => {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE}/notifications/${notificationId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to delete notification');
    return response.json();
  },

  deleteAllRead: async () => {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE}/notifications/delete-all-read`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to delete read notifications');
    return response.json();
  },

  generateAuto: async () => {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE}/notifications/generate-auto`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to generate notifications');
    return response.json();
  },

  getTypes: async () => {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE}/notifications/types`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to fetch notification types');
    return response.json();
  },
};
