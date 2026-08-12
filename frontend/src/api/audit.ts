import { API_BASE } from '../api/client';

export const auditApi = {
  getAll: async (params: {
    limit?: number;
    offset?: number;
    entity_type?: string;
    action?: string;
    user_id?: number;
    start_date?: string;
    end_date?: string;
    search?: string;
  } = {}) => {
    const token = localStorage.getItem('token');
    const searchParams = new URLSearchParams();
    if (params.limit) searchParams.set('limit', String(params.limit));
    if (params.offset) searchParams.set('offset', String(params.offset));
    if (params.entity_type) searchParams.set('entity_type', params.entity_type);
    if (params.action) searchParams.set('action', params.action);
    if (params.user_id) searchParams.set('user_id', String(params.user_id));
    if (params.start_date) searchParams.set('start_date', params.start_date);
    if (params.end_date) searchParams.set('end_date', params.end_date);
    if (params.search) searchParams.set('search', params.search);

    const response = await fetch(`${API_BASE}/audit/?${searchParams}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to fetch audit log');
    return response.json();
  },

  getSummary: async () => {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE}/audit/summary`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to fetch audit summary');
    return response.json();
  },

  getStatsOverview: async () => {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE}/audit/stats/overview`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to fetch audit stats');
    return response.json();
  },

  getHistory: async (entityType: string, entityId: number, limit = 50, offset = 0) => {
    const token = localStorage.getItem('token');
    const response = await fetch(
      `${API_BASE}/audit/${entityType}/${entityId}/history?limit=${limit}&offset=${offset}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (!response.ok) throw new Error('Failed to fetch entity history');
    return response.json();
  },
};
