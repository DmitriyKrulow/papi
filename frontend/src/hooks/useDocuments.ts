import { useState, useEffect, useCallback } from 'react';
import axios, { AxiosError } from 'axios';

interface Document {
  id: number;
  filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  uploaded_by: number;
  document_type: string;
  category: string;
  entity_id?: number;
  entity_type?: string;
  title?: string;
  description?: string;
  uploaded_at: string;
  is_primary: boolean;
  sort_order: number;
  file_hash?: string;
}

interface DocumentListResponse {
  total: number;
  items: Document[];
}

interface UploadData {
  document_type?: string;
  category?: string;
  entity_id?: number;
  entity_type?: string;
  title?: string;
  description?: string;
  is_primary?: boolean;
  sort_order?: number;
}

export const useDocuments = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState<number>(0);

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get<DocumentListResponse>('/api/documents');
      setDocuments(response.data.items);
      setTotal(response.data.total || response.data.items.length);
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || 'Failed to fetch documents');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDocumentById = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get<Document>(`/api/documents/${id}`);
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to fetch document with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const uploadDocument = useCallback(async (file: File, data?: UploadData) => {
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      if (data) {
        if (data.document_type) formData.append('document_type', data.document_type);
        if (data.category) formData.append('category', data.category);
        if (data.entity_id !== undefined && data.entity_id !== null) {
          formData.append('entity_id', String(data.entity_id));
        }
        if (data.entity_type) formData.append('entity_type', data.entity_type);
        if (data.title) formData.append('title', data.title);
        if (data.description) formData.append('description', data.description);
        if (data.is_primary !== undefined) formData.append('is_primary', String(data.is_primary));
        if (data.sort_order !== undefined && data.sort_order !== null) {
          formData.append('sort_order', String(data.sort_order));
        }
      }
      
      const response = await axios.post<Document>('/api/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setDocuments((prev) => [...prev, response.data]);
      return response.data;
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || 'Failed to upload document');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteDocument = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      await axios.delete(`/api/documents/${id}`);
      setDocuments((prev) => prev.filter((doc) => doc.id !== id));
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(axiosError.message || `Failed to delete document with id ${id}`);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  return {
    documents,
    loading,
    error,
    total,
    fetchDocuments,
    fetchDocumentById,
    uploadDocument,
    deleteDocument,
  };
};
