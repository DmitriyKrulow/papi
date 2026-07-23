import { useState, useEffect, useCallback } from 'react';
import axios, { AxiosError } from 'axios';

export interface AssetPhoto {
  id: number;
  asset_id: number;
  document_id: number;
  uploaded_by: number;
  stage: string;
  description?: string;
  taken_at?: string;
  taken_by?: number;
  inventory_check_id?: number;
  repair_request_id?: number;
  is_before: boolean;
  is_after: boolean;
  sort_order: number;
  uploaded_at: string;
}

export interface AssetPhotoListResponse {
  total: number;
  items: AssetPhoto[];
}

export const useAssetPhotos = (assetId: number) => {
  const [photos, setPhotos] = useState<AssetPhoto[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);

  const fetchPhotos = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get<AssetPhotoListResponse>(`/api/assets/${assetId}/photos`);
      setPhotos(response.data.items || []);
      setTotal(response.data.total || (response.data.items ? response.data.items.length : 0));
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || 'Failed to fetch asset photos');
    } finally {
      setLoading(false);
    }
  }, [assetId]);

  const fetchPhotoById = useCallback(async (photoId: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get<AssetPhoto>(`/api/asset-photos/${photoId}`);
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to fetch photo with id ${photoId}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const uploadPhoto = useCallback(async (file: File, data?: any) => {
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      if (data) {
        if (data.stage) formData.append('stage', data.stage);
        if (data.description) formData.append('description', data.description);
        if (data.taken_at) formData.append('taken_at', data.taken_at);
        if (data.taken_by !== undefined && data.taken_by !== null) {
          formData.append('taken_by', String(data.taken_by));
        }
        if (data.inventory_check_id !== undefined && data.inventory_check_id !== null) {
          formData.append('inventory_check_id', String(data.inventory_check_id));
        }
        if (data.repair_request_id !== undefined && data.repair_request_id !== null) {
          formData.append('repair_request_id', String(data.repair_request_id));
        }
        if (data.is_before !== undefined) formData.append('is_before', String(data.is_before));
        if (data.is_after !== undefined) formData.append('is_after', String(data.is_after));
        if (data.sort_order !== undefined && data.sort_order !== null) {
          formData.append('sort_order', String(data.sort_order));
        }
      }
      
      const response = await axios.post<AssetPhoto>(`/asset-photos/${assetId}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setPhotos((prev) => [...prev, response.data]);
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || 'Failed to upload photo');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [assetId]);

  const deletePhoto = useCallback(async (photoId: number) => {
    setLoading(true);
    setError(null);
    try {
      await axios.delete(`/api/asset-photos/${photoId}`);
      setPhotos((prev) => prev.filter((photo) => photo.id !== photoId));
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to delete photo with id ${photoId}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPhotos();
  }, [fetchPhotos]);

  return {
    photos,
    loading,
    error,
    total,
    fetchPhotos,
    fetchPhotoById,
    uploadPhoto,
    deletePhoto,
  };
};
