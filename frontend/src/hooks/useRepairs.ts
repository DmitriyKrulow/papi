import { useState, useEffect, useCallback } from 'react';
import { AxiosError } from 'axios';
import { apiClient } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import { useAssets } from '../hooks/useAssets';
import type { RepairRequest } from '../types';

export const useRepairs = () => {
  const { user } = useAuth();
  const token = localStorage.getItem('token');
  console.log('[useRepairs] user:', user?.username);
  console.log('[useRepairs] token:', token ? token.substring(0, 20) + '...' : 'NONE');
  const [repairs, setRepairs] = useState<RepairRequest[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);
  
  // Вызываем useAssets для обновления активов при изменении статуса заявки
  const { fetchAssets } = useAssets();

  const repairTemplates = [
    {
      id: 'template_electrical',
      title: 'Электрические проблемы',
      description: 'Проблемы с электрическими цепями, проводкой, розетками',
    },
    {
      id: 'template_mechanical',
      title: 'Механические повреждения',
      description: 'Износ механизмов, шум, вибрация, скрипы',
    },
    {
      id: 'template_software',
      title: 'Проблемы ПО',
      description: 'Сбои в программном обеспечении, обновления',
    },
    {
      id: 'template_network',
      title: 'Сетевые проблемы',
      description: 'Проблемы с сетевым подключением, маршрутизацией',
    },
    {
      id: 'template_hvac',
      title: 'Климатическое оборудование',
      description: 'Проблемы с отоплением, вентиляцией, кондиционированием',
    },
    {
      id: 'template_safety',
      title: 'Системы безопасности',
      description: 'Проблемы с охраной, пожарной сигнализацией, видеонаблюдением',
    },
  ];

  const fetchRepairs = useCallback(async () => {
    console.log('[useRepairs] fetchRepairs called');
    console.log('[useRepairs] Token before fetch:', localStorage.getItem('token') ? localStorage.getItem('token')!.substring(0, 30) + '...' : 'NONE');
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.repairs.list();
      console.log('[useRepairs] fetchRepairs success, items count:', response.data.items?.length);
      setRepairs(response.data.items);
      setTotal(response.data.total);
    } catch (err) {
      const axiosError = err as AxiosError;
      console.error('[useRepairs] fetchRepairs error:', axiosError.response?.status, axiosError.response?.data);
      setError(axiosError.message || 'Failed to fetch repairs');
    } finally {
      setLoading(false);
    }
  }, []);

  const createRepair = useCallback(async (repairData: any) => {
    console.log('[useRepairs] createRepair called with:', repairData);
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.repairs.create(repairData);
      console.log('[useRepairs] createRepair success:', response.data);
      setRepairs((prev) => [...prev, response.data]);
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      console.error('[useRepairs] createRepair error status:', axiosError.response?.status);
      console.error('[useRepairs] createRepair error data:', axiosError.response?.data);
      if (axiosError.response?.data && typeof axiosError.response.data === 'object' && 'detail' in axiosError.response.data) {
        console.error('[useRepairs] createRepair error detail:', (axiosError.response.data as any).detail);
      }
      console.error('[useRepairs] createRepair error message:', axiosError.message);
      setError(String(axiosError.response?.data || axiosError.message || 'Failed to create repair'));
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateRepair = useCallback(async (id: number, repairData: Partial<RepairRequest>) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.repairs.update(id, repairData);
      setRepairs((prev) => prev.map((repair) => (repair.id === id ? response.data : repair)));
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to update repair with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateRepairStatus = useCallback(async (id: number, status: string) => {
    console.log('[useRepairs] updateRepairStatus called with id:', id, 'status:', status);
    const token = localStorage.getItem('token');
    console.log('[useRepairs] Token in localStorage:', token ? token.substring(0, 30) + '...' : 'NONE');
    console.log('[useRepairs] Token first 50 chars:', token?.substring(0, 50));
    console.log('[useRepairs] Token length:', token?.length);
    console.log('[useRepairs] localStorage keys:', Object.keys(localStorage));
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.repairs.updateStatus(id, status);
      console.log('[useRepairs] updateRepairStatus success:', response.data);
      setRepairs((prev) => prev.map((repair) => (repair.id === id ? response.data : repair)));
      // Обновляем активы после изменения статуса заявки
      console.log('[useRepairs] Calling fetchAssets to update asset status...');
      fetchAssets();
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      console.error('[useRepairs] updateRepairStatus error status:', axiosError.response?.status);
      console.error('[useRepairs] updateRepairStatus error data:', axiosError.response?.data);
      console.error('[useRepairs] updateRepairStatus error headers:', axiosError.response?.headers);
      setError(axiosError.message || `Failed to update repair status with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchAssets]);

  const updateRepairPriority = useCallback(async (id: number, priority: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.repairs.updatePriority(id, priority);
      setRepairs((prev) => prev.map((repair) => (repair.id === id ? response.data : repair)));
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to update repair priority with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteRepair = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      await apiClient.repairs.delete(id);
      setRepairs((prev) => prev.filter((repair) => repair.id !== id));
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to delete repair with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchRepairById = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.repairs.get(id);
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to fetch repair with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

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
    repairTemplates,
  };
};
