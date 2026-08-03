// frontend/src/components/assets/AssetDocuments.tsx
import { useState, useEffect, useCallback } from 'react';
import { FileText, Upload, Download, Trash2, Link, ExternalLink, Search, File as FileIcon } from 'lucide-react';
import toast from 'react-hot-toast';

interface AssetDocument {
  id: number;
  filename: string;
  file_size: number;
  mime_type: string;
  document_type: string;
  title: string | null;
  description: string | null;
  uploaded_at: string;
  uploaded_by: number;
  linked_asset_ids: number[];
  link_count: number;
}

interface AssetDocumentsProps {
  assetId: number;
  assetName?: string;
}

const DOCUMENT_TYPES: Record<string, { label: string; icon: string }> = {
  order: { label: 'Приказ', icon: '📋' },
  invoice: { label: 'Накладная', icon: '📄' },
  receipt: { label: 'Расписка', icon: '✍️' },
  assignment: { label: 'Назначение', icon: '📌' },
  other: { label: 'Прочее', icon: '📎' },
};

const getFileIcon = (mimeType: string): string => {
  if (mimeType.startsWith('image/')) return '🖼️';
  if (mimeType === 'application/pdf') return '📕';
  if (mimeType.includes('spreadsheet') || mimeType.includes('excel')) return '📊';
  if (mimeType.includes('word') || mimeType.includes('document')) return '📝';
  if (mimeType.includes('zip') || mimeType.includes('rar') || mimeType.includes('7z')) return '📦';
  return '📎';
};

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const AssetDocuments: React.FC<AssetDocumentsProps> = ({ assetId, assetName }) => {
  const [documents, setDocuments] = useState<AssetDocument[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [documentType, setDocumentType] = useState('other');
  const [documentTitle, setDocumentTitle] = useState('');
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({ asset_id: String(assetId) });
      if (searchQuery) params.set('search', searchQuery);
      const res = await fetch(`/api/asset-documents/?${params}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.items || []);
      }
    } catch (err) {
      console.error('Error fetching documents:', err);
    } finally {
      setLoading(false);
    }
  }, [assetId, searchQuery]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    const fileInput = document.getElementById('asset-doc-file') as HTMLInputElement;
    const file = fileInput?.files?.[0];
    if (!file) {
      toast.error('Выберите файл');
      return;
    }

    setUploading(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        toast.error('Не авторизован');
        return;
      }

      const formData = new FormData();
      formData.append('file', file);
      formData.append('asset_ids', JSON.stringify([assetId]));
      formData.append('document_type', documentType);
      if (documentTitle.trim()) formData.append('title', documentTitle.trim());

      const res = await fetch('/api/asset-documents/upload', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });

      if (res.ok) {
        toast.success('Документ загружен');
        setShowUploadForm(false);
        setDocumentTitle('');
        setDocumentType('other');
        fileInput.value = '';
        fetchDocuments();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Ошибка загрузки');
      }
    } catch (err) {
      toast.error('Ошибка соединения');
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = (doc: AssetDocument) => {
    const token = localStorage.getItem('token');
    const url = `/api/asset-documents/${doc.id}/download`;
    window.open(url, '_blank');
  };

  const handleUnlink = async (doc: AssetDocument) => {
    if (!confirm(`Отвязать документ "${doc.title || doc.filename}" от этого актива?\n\nЕсли документ больше не привязан ни к одному активу — он будет удалён.`)) return;

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(
        `/api/asset-documents/${doc.id}/unlink?asset_ids=${encodeURIComponent(JSON.stringify([assetId]))}`,
        {
          method: 'DELETE',
          headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        }
      );

      if (res.ok) {
        const data = await res.json();
        if (data.document_deleted) {
          toast.success('Документ удалён (больше не привязан ни к одному активу)');
        } else {
          toast.success('Документ отвязан от актива');
        }
        fetchDocuments();
      } else {
        toast.error('Ошибка отвязки');
      }
    } catch (err) {
      toast.error('Ошибка соединения');
    }
  };

  const handleForceDelete = async (doc: AssetDocument) => {
    if (!confirm(`ПОЛНОСТЬЮ удалить документ "${doc.title || doc.filename}"?\n\nОн будет удалён со всех активов и с диска. Это действие необратимо.`)) return;

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/asset-documents/${doc.id}`, {
        method: 'DELETE',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      });

      if (res.ok) {
        toast.success('Документ полностью удалён');
        fetchDocuments();
      } else {
        toast.error('Ошибка удаления');
      }
    } catch (err) {
      toast.error('Ошибка соединения');
    }
  };

  const getDocTypeLabel = (type: string) => {
    return DOCUMENT_TYPES[type] || DOCUMENT_TYPES.other;
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide flex items-center gap-2">
          <FileText className="w-4 h-4" />
          Документы
          {documents.length > 0 && (
            <span className="text-xs font-normal text-gray-400">({documents.length})</span>
          )}
        </h4>
        <button
          onClick={() => setShowUploadForm(!showUploadForm)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700 transition"
        >
          <Upload className="w-3 h-3" />
          {showUploadForm ? 'Отмена' : 'Загрузить'}
        </button>
      </div>

      {/* Upload Form */}
      {showUploadForm && (
        <form onSubmit={handleUpload} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Тип документа</label>
              <select
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              >
                {Object.entries(DOCUMENT_TYPES).map(([key, val]) => (
                  <option key={key} value={key}>{val.icon} {val.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Название (необязательно)</label>
              <input
                type="text"
                value={documentTitle}
                onChange={(e) => setDocumentTitle(e.target.value)}
                placeholder="Например: Приказ №45 от 01.03.2024"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Файл</label>
            <input
              id="asset-doc-file"
              type="file"
              accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx,.txt,.zip,.rar"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-sm file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            <p className="text-xs text-gray-400 mt-1">PDF, JPG, PNG, DOC, XLS, ZIP — до 50 МБ</p>
          </div>
          <button
            type="submit"
            disabled={uploading}
            className="w-full px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? '⏳ Загрузка...' : '📤 Загрузить и привязать'}
          </button>
        </form>
      )}

      {/* Search */}
      {documents.length > 0 && (
        <div className="relative">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Поиск по названию файла..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
        </div>
      )}

      {/* Document List */}
      {loading ? (
        <div className="flex justify-center py-6">
          <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <span className="ml-2 text-sm text-gray-500">Загрузка...</span>
        </div>
      ) : documents.length === 0 ? (
        <div className="text-center py-6 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
          <div className="text-3xl mb-2">📄</div>
          <p className="text-sm text-gray-500 dark:text-gray-400">Нет привязанных документов</p>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
            Загрузите приказы, накладные, расписки и другие файлы
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {documents.map((doc) => {
            const typeInfo = getDocTypeLabel(doc.document_type);
            return (
              <div
                key={doc.id}
                className="flex items-center gap-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:shadow-sm transition group"
              >
                {/* Icon */}
                <div className="flex-shrink-0 w-10 h-10 flex items-center justify-center bg-gray-100 dark:bg-gray-700 rounded-lg text-lg">
                  {getFileIcon(doc.mime_type)}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 font-medium">
                      {typeInfo.icon} {typeInfo.label}
                    </span>
                    {doc.link_count > 1 && (
                      <span className="text-xs text-blue-500 flex items-center gap-0.5">
                        <Link className="w-3 h-3" />
                        {doc.link_count} актива
                      </span>
                    )}
                  </div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                    {doc.title || doc.filename}
                  </p>
                  <div className="flex items-center gap-3 text-xs text-gray-400 dark:text-gray-500">
                    <span>{doc.filename}</span>
                    <span>{formatFileSize(doc.file_size)}</span>
                    <span>{new Date(doc.uploaded_at).toLocaleDateString('ru-RU')}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex-shrink-0 flex items-center gap-1 opacity-60 group-hover:opacity-100 transition">
                  <button
                    onClick={() => handleDownload(doc)}
                    className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-gray-700 rounded-lg transition"
                    title="Скачать/просмотреть"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleUnlink(doc)}
                    className="p-1.5 text-gray-400 hover:text-orange-600 hover:bg-orange-50 dark:hover:bg-gray-700 rounded-lg transition"
                    title="Отвязать от актива"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default AssetDocuments;