import { useState, useEffect, useCallback } from 'react';
import axios, { AxiosError } from 'axios';
import { useAuth } from './useAuth';

interface Department {
  id: number;
  organization_id: number;
  name: string;
  code: string;
  parent_id?: number;
  head?: string;
  phone?: string;
  email?: string;
  location?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface DepartmentCreate {
  organization_id: number;
  name: string;
  code: string;
  parent_id?: number;
  head?: string;
  phone?: string;
  email?: string;
  location?: string;
  is_active?: boolean;
}

interface DepartmentUpdate {
  name?: string;
  code?: string;
  parent_id?: number;
  head?: string;
  phone?: string;
  email?: string;
  location?: string;
  is_active?: boolean;
}

export const useDepartments = () => {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const { getToken } = useAuth();

  const fetchDepartments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await axios.get<Department[]>('/api/departments', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setDepartments(response.data);
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || 'Failed to fetch departments');
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const fetchDepartmentById = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await axios.get<Department>(`/api/departments/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to fetch department with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const fetchDepartmentByCode = useCallback(async (code: string) => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await axios.get<Department>(`/api/departments/code/${code}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to fetch department with code ${code}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const createDepartment = useCallback(async (departmentData: DepartmentCreate) => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await axios.post<Department>('/api/departments', departmentData, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setDepartments((prev) => [...prev, response.data]);
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || 'Failed to create department');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const updateDepartment = useCallback(async (id: number, departmentData: DepartmentUpdate) => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await axios.put<Department>(`/api/departments/${id}`, departmentData, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setDepartments((prev) => prev.map((dept) => (dept.id === id ? response.data : dept)));
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to update department with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const deleteDepartment = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      await axios.delete(`/api/departments/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setDepartments((prev) => prev.filter((dept) => dept.id !== id));
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to delete department with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    fetchDepartments();
  }, [fetchDepartments]);

  return {
    departments,
    loading,
    error,
    fetchDepartments,
    fetchDepartmentById,
    fetchDepartmentByCode,
    createDepartment,
    updateDepartment,
    deleteDepartment,
  };
};
