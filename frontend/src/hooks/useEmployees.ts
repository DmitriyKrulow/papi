import { useState, useEffect, useCallback } from 'react';
import axios, { AxiosError } from 'axios';
import { useAuth } from './useAuth';

interface Employee {
  id: number;
  department_id: number;
  user_id: number;
  first_name: string;
  last_name: string;
  middle_name?: string;
  phone?: string;
  email?: string;
  position?: string;
  position_code?: string;
  employee_number?: string;
  hire_date?: string;
  termination_date?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface EmployeeCreate {
  department_id: number;
  user_id: number;
  first_name: string;
  last_name: string;
  middle_name?: string;
  phone?: string;
  email?: string;
  position?: string;
  position_code?: string;
  employee_number?: string;
  hire_date?: string;
  termination_date?: string;
  is_active?: boolean;
}

interface EmployeeUpdate {
  department_id?: number;
  user_id?: number;
  first_name?: string;
  last_name?: string;
  middle_name?: string;
  phone?: string;
  email?: string;
  position?: string;
  position_code?: string;
  employee_number?: string;
  hire_date?: string;
  termination_date?: string;
  is_active?: boolean;
}

export const useEmployees = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const { getToken } = useAuth();

  const fetchEmployees = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await axios.get<Employee[]>('/api/employees', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setEmployees(response.data);
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || 'Failed to fetch employees');
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const fetchEmployeeById = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await axios.get<Employee>(`/api/employees/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to fetch employee with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const createEmployee = useCallback(async (employeeData: EmployeeCreate) => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await axios.post<Employee>('/api/employees', employeeData, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setEmployees((prev) => [...prev, response.data]);
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || 'Failed to create employee');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const updateEmployee = useCallback(async (id: number, employeeData: EmployeeUpdate) => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await axios.put<Employee>(`/api/employees/${id}`, employeeData, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setEmployees((prev) => prev.map((emp) => (emp.id === id ? response.data : emp)));
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to update employee with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const deleteEmployee = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      await axios.delete(`/api/employees/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setEmployees((prev) => prev.filter((emp) => emp.id !== id));
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to delete employee with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);

  return {
    employees,
    loading,
    error,
    fetchEmployees,
    fetchEmployeeById,
    createEmployee,
    updateEmployee,
    deleteEmployee,
  };
};
