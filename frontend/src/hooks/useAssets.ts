import { useState, useEffect, useCallback } from 'react';
import axios, { AxiosError } from 'axios';
import { useAuth } from './useAuth';

interface Asset {
  id: number;
  inventory_number: string;
  name: string;
  description?: string;
  model?: string;
  manufacturer_code?: string;
  manufacturer_name?: string;
  country_of_origin?: string;
  accounting_code?: string;
  department_code?: string;
  responsible_person?: string;
  purchase_price?: number;
  current_value?: number;
  residual_value?: number;
  depreciation_rate?: number;
  location?: string;
  location_address?: string;
  responsible_phone?: string;
  purchase_date?: string;
  commissioning_date?: string;
  warranty_expiry?: string;
  last_maintenance_date?: string;
  next_maintenance_date?: string;
  decommissioning_date?: string;
  status: string;
  created_at: string;
  updated_at: string;
  created_by?: number;
  updated_by?: number;
  tags?: string[];
  notes?: string;
  is_active: boolean;
}

interface AssetListResponse {
  total: number;
  items: Asset[];
}

interface AssetCreate {
  inventory_number: string;
  name: string;
  description?: string;
  model?: string;
  manufacturer_code?: string;
  manufacturer_name?: string;
  country_of_origin?: string;
  accounting_code?: string;
  department_code?: string;
  responsible_person?: string;
  purchase_price?: number;
  current_value?: number;
  residual_value?: number;
  depreciation_rate?: number;
  location?: string;
  location_address?: string;
  responsible_phone?: string;
  purchase_date?: string;
  commissioning_date?: string;
  warranty_expiry?: string;
  last_maintenance_date?: string;
  next_maintenance_date?: string;
  decommissioning_date?: string;
  tags?: string[];
  notes?: string;
  is_active?: boolean;
}

interface AssetUpdate {
  name?: string;
  description?: string;
  model?: string;
  manufacturer_code?: string;
  manufacturer_name?: string;
  country_of_origin?: string;
  accounting_code?: string;
  department_code?: string;
  responsible_person?: string;
  purchase_price?: number;
  current_value?: number;
  residual_value?: number;
  depreciation_rate?: number;
  location?: string;
  location_address?: string;
  responsible_phone?: string;
  purchase_date?: string;
  commissioning_date?: string;
  warranty_expiry?: string;
  last_maintenance_date?: string;
  next_maintenance_date?: string;
  decommissioning_date?: string;
  status?: string;
  tags?: string[];
  notes?: string;
  is_active?: boolean;
}

export const useAssets = () => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);
  const { getToken } = useAuth();

  const fetchAssets = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await axios.get<AssetListResponse>('/api/assets', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setAssets(response.data.items);
      setTotal(response.data.total);
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || 'Failed to fetch assets');
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const fetchAssetById = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await axios.get<Asset>(`/api/assets/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to fetch asset with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const createAsset = useCallback(async (assetData: AssetCreate) => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await axios.post<Asset>('/api/assets', assetData, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setAssets((prev) => [...prev, response.data]);
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || 'Failed to create asset');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const updateAsset = useCallback(async (id: number, assetData: AssetUpdate) => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const response = await axios.put<Asset>(`/api/assets/${id}`, assetData, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setAssets((prev) => prev.map((asset) => (asset.id === id ? response.data : asset)));
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to update asset with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const deleteAsset = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      await axios.delete(`/api/assets/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setAssets((prev) => prev.filter((asset) => asset.id !== id));
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to delete asset with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    fetchAssets();
  }, [fetchAssets]);

  return {
    assets,
    loading,
    error,
    total,
    fetchAssets,
    fetchAssetById,
    createAsset,
    updateAsset,
    deleteAsset,
  };
};
