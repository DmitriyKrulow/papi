import { useState, useCallback } from 'react';
import { useDocuments } from '../hooks/useDocuments';

interface FileUploadProps {
  onUploadSuccess?: (document: any) => void;
  allowedExtensions?: string[];
  maxSizeMB?: number;
  showFilesAfterUpload?: boolean;
}

export const FileUpload = ({
  onUploadSuccess,
  allowedExtensions = [],
  maxSizeMB = 10,
  showFilesAfterUpload = false,
}: FileUploadProps) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const { uploadDocument, error } = useDocuments();

  const validateFile = (file: File): boolean => {
    if (allowedExtensions.length > 0) {
      const fileExtension = '.' + file.name.split('.').pop();
      if (!allowedExtensions.some(ext => fileExtension.toLowerCase() === ext.toLowerCase())) {
        setUploadError(`Недопустимый формат файла. Разрешенные: ${allowedExtensions.join(', ')}`);
        return false;
      }
    }

    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      setUploadError(`Размер файла превышает лимит ${maxSizeMB} МБ`);
      return false;
    }

    return true;
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      setUploadError(null);

      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        const file = e.dataTransfer.files[0];
        if (validateFile(file)) {
          await handleUpload(file);
        }
      }
    },
    [],
  );

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        const file = e.target.files[0];
        if (validateFile(file)) {
          await handleUpload(file);
        }
      }
      e.target.value = '';
    },
    [],
  );

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setUploadError(null);

    try {
      const document = await uploadDocument(file);
      if (onUploadSuccess) {
        onUploadSuccess(document);
      }
    } catch (err) {
      console.error('Upload error:', err);
    } finally {
      setIsUploading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="file-upload">
      <div
        className={`drop-zone ${isDragging ? 'dragging' : ''} ${uploadError ? 'error' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-input"
          className="file-input"
          onChange={handleFileSelect}
          disabled={isUploading}
        />
        <label htmlFor="file-input" className="drop-zone-label">
          {isUploading ? (
            <span className="loading">⏳ Загрузка...</span>
          ) : uploadError ? (
            <span className="error-text">❌ {uploadError}</span>
          ) : (
            <>
              <span className="icon">📁</span>
              <span className="text">Перетащите файл сюда или кликните для выбора</span>
              {allowedExtensions.length > 0 && (
                <span className="hint">Разрешенные форматы: {allowedExtensions.join(', ')}</span>
              )}
              <span className="hint">Максимальный размер: {maxSizeMB} MB</span>
            </>
          )}
        </label>
      </div>

      {showFilesAfterUpload && error && (
        <div className="upload-error">
          <span>❌ {error}</span>
        </div>
      )}
    </div>
  );
};
