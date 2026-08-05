// frontend/src/components/assets/ImportAssetsModal.tsx
import React, { useState } from 'react';
import toast from 'react-hot-toast';

interface ImportAssetsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const ImportAssetsModal: React.FC<ImportAssetsModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);

  if (!isOpen) return null;

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      validateAndSetFile(droppedFile);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (file: File) => {
    const validExtensions = ['.xlsx', '.xls'];
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!validExtensions.includes(extension || '')) {
      toast.error('Пожалуйста, загрузите файл Excel (.xlsx или .xls)');
      return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
      toast.error('Файл слишком большой. Максимальный размер 10 MB');
      return;
    }
    
    setFile(file);
    setImportResult(null);
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error('Выберите файл для загрузки');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('token');
      console.log('[ImportAssetsModal] Token:', token?.substring(0, 50) + '...');
      console.log('[ImportAssetsModal] File:', file.name, file.size);
      
      const response = await fetch('/api/inventory-import/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/json',
        },
        body: formData,
      });

      console.log('[ImportAssetsModal] Response status:', response.status);
      console.log('[ImportAssetsModal] Response headers:', Object.fromEntries(response.headers.entries()));

      const data = await response.json();
      
      if (response.ok) {
        setImportResult(data);
        toast.success(`Импорт успешно завершен! Добавлено ${data.processed_rows || 0} активов`);
        
        if (onSuccess) {
          onSuccess();
        }
      } else {
        console.error('[ImportAssetsModal] Error response:', data);
        toast.error(data.detail || 'Ошибка при загрузке файла');
      }
    } catch (error) {
      console.error('[ImportAssetsModal] Upload error:', error);
      toast.error('Ошибка соединения с сервером');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setImportResult(null);
    setLoading(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 dark:bg-gray-600 opacity-75 dark:opacity-80" onClick={handleClose}></div>
        </div>

        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">
          &#8203;
        </span>

        <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
          <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">📤 Загрузка активов из файла</h3>
              <button
                onClick={handleClose}
                className="text-gray-400 dark:text-gray-500 dark:text-gray-400 hover:text-gray-500 dark:text-gray-400 focus:outline-none"
              >
                <span className="sr-only">Закрыть</span>
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {!importResult ? (
              <>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                  Загрузите файл инвентаризационной описи в формате Excel (.xlsx, .xls)
                </p>

                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center ${
                    dragActive ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-gray-600'
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  {file ? (
                    <div className="space-y-2">
                      <div className="text-4xl">📄</div>
                      <p className="font-medium text-gray-700 dark:text-gray-200">{file.name}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {(file.size / 1024).toFixed(1)} KB
                      </p>
                      <button
                        onClick={() => setFile(null)}
                        className="text-red-500 hover:text-red-700 text-sm"
                      >
                        Удалить файл
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="text-4xl mb-2">📂</div>
                      <p className="text-gray-600 dark:text-gray-300">
                        Перетащите файл сюда или кликните для выбора
                      </p>
                      <p className="text-sm text-gray-400 dark:text-gray-500 dark:text-gray-400 mt-1">
                        Поддерживаются файлы .xlsx, .xls (макс. 10 MB)
                      </p>
                      <input
                        type="file"
                        accept=".xlsx,.xls"
                        onChange={handleFileChange}
                        className="hidden"
                        id="file-upload"
                      />
                      <label
                        htmlFor="file-upload"
                        className="inline-block mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition cursor-pointer"
                      >
                        Выбрать файл
                      </label>
                    </>
                  )}
                </div>

                <div className="mt-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
                  <p className="text-sm text-yellow-700 dark:text-yellow-200">
                    ⚠️ Файл должен соответствовать формату инвентаризационной описи (форма 0510466)
                  </p>
                </div>

                <div className="mt-6 flex justify-end space-x-3">
                  <button
                    onClick={handleClose}
                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                  >
                    Отмена
                  </button>
                  <button
                    onClick={handleUpload}
                    disabled={!file || loading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <>
                        <span className="animate-spin inline-block mr-2">⏳</span>
                        Загрузка...
                      </>
                    ) : (
                      'Загрузить'
                    )}
                  </button>
                </div>
              </>
            ) : (
              <div className="space-y-4">
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                  <h4 className="text-green-800 dark:text-green-200 font-medium mb-2">✅ Импорт запущен!</h4>
                  <div className="space-y-1 text-sm text-green-700 dark:text-green-300">
                    <p>📊 Всего строк: {importResult.total_rows || 0}</p>
                    <p>✅ Валидных: {importResult.valid_rows || 0}</p>
                    <p>❌ Ошибок: {importResult.errors || 0}</p>
                    <p>📁 Файл: {importResult.filename || '—'}</p>
                  </div>
                </div>

                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                  <p className="text-sm text-blue-700 dark:text-blue-300">
                    ℹ️ Импорт выполняется в фоновом режиме. Проверьте статус в разделе отчетов.
                  </p>
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    onClick={handleClose}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                  >
                    Закрыть
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImportAssetsModal;