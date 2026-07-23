import { useState, useEffect, useCallback } from 'react';
import axios, { AxiosError } from 'axios';
import { useAuth } from './useAuth';

interface RepairPriority {
  LOW: 'low';
  MEDIUM: 'medium';
  HIGH: 'high';
  URGENT: 'urgent';
}

interface RepairStatus {
  DRAFT: 'draft';
  SUBMITTED: 'submitted';
  APPROVED: 'approved';
  IN_PROGRESS: 'in_progress';
  COMPLETED: 'completed';
  REJECTED: 'rejected';
  CANCELLED: 'cancelled';
}

interface Repair {
  id: number;
  asset_id: number;
  title: string;
  description: string;
  priority: RepairPriority[keyof RepairPriority];
  status: RepairStatus[keyof RepairStatus];
  created_at: string;
  created_by: number;
  assigned_to?: number;
  assigned_at?: string;
  desired_completion_date?: string;
  actual_completion_date?: string;
  deadline?: string;
  estimated_cost?: number;
  actual_cost?: number;
  completion_notes?: string;
  rejection_reason?: string;
  maintenance_record_id?: number;
  updated_at: string;
  updated_by?: number;
}

interface RepairListResponse {
  total: number;
  items: Repair[];
}

interface RepairCreate {
  asset_id: number;
  title: string;
  description: string;
  priority?: RepairPriority[keyof RepairPriority];
  created_by: number;
  desired_completion_date?: string;
  deadline?: string;
  estimated_cost?: number;
}

interface RepairUpdate {
  title?: string;
  description?: string;
  priority?: RepairPriority[keyof RepairPriority];
  assigned_to?: number;
  desired_completion_date?: string;
  actual_completion_date?: string;
  deadline?: string;
  estimated_cost?: number;
  actual_cost?: number;
  completion_notes?: string;
  rejection_reason?: string;
  maintenance_record_id?: number;
  updated_by?: number;
}

export const useRepairs = () => {
  const [repairs, setRepairs] = useState<Repair[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);
  const { getToken } = useAuth();

  const fetchRepairs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await axios.get<RepairListResponse>('/api/repairs', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setRepairs(response.data.items);
      setTotal(response.data.total);
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || 'Failed to fetch repairs');
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const fetchRepairById = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await axios.get<Repair>(`/api/repairs/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to fetch repair with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const createRepair = useCallback(async (repairData: RepairCreate) => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await axios.post<Repair>('/api/repairs', repairData, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setRepairs((prev) => [...prev, response.data]);
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || 'Failed to create repair');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const updateRepair = useCallback(async (id: number, repairData: RepairUpdate) => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await axios.put<Repair>(`/api/repairs/${id}`, repairData, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setRepairs((prev) => prev.map((repair) => (repair.id === id ? response.data : repair)));
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to update repair with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const updateRepairStatus = useCallback(async (id: number, status: string) => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await axios.patch<Repair>(`/api/repairs/${id}/status`, { status }, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setRepairs((prev) => prev.map((repair) => (repair.id === id ? response.data : repair)));
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to update repair status with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const updateRepairPriority = useCallback(async (id: number, priority: string) => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await axios.patch<Repair>(`/api/repairs/${id}/priority`, { priority }, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setRepairs((prev) => prev.map((repair) => (repair.id === id ? response.data : repair)));
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to update repair priority with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const deleteRepair = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      await axios.delete(`/api/repairs/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setRepairs((prev) => prev.filter((repair) => repair.id !== id));
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to delete repair with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    fetchRepairs();
  }, [fetchRepairs]);

  return {
    repairs,
    loading,
    error,
    total,
    fetchRepairs,
    fetchRepairById,
    createRepair,
    updateRepair,
    updateRepairStatus,
    updateRepairPriority,
    deleteRepair,
  };
};
