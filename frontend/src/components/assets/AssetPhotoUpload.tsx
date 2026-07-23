import { useState } from 'react';
import { useAssetPhotos } from '../hooks/useAssetPhotos';

interface AssetPhotoUploadProps {
  assetId: number;
  stage?: string;
  onUploadSuccess?: (photo: any) => void;
  allowedExtensions?: string[];
  maxSizeMB?: number;
  showPreviews?: boolean;
}

export const AssetPhotoUpload = ({
  assetId,
  stage = 'other',
  onUploadSuccess,
  allowedExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
  maxSizeMB = 5,
  showPreviews = true,
}: AssetPhotoUploadProps) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const { uploadPhoto, error } = useAssetPhotos(assetId);

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

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    setUploadError(null);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        await handleUpload(file);
      }
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        await handleUpload(file);
      }
    }
    e.target.value = '';
  };

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setUploadError(null);

    try {
      const photo = await uploadPhoto(file, {
        stage,
        description: `Загружено: ${file.name}`,
        taken_at: new Date().toISOString(),
      });
      
      if (onUploadSuccess) {
        onUploadSuccess(photo);
      }
    } catch (err) {
      console.error('Upload error:', err);
      setUploadError('Ошибка при загрузке фотографии');
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
    <div className="asset-photo-upload">
      <div
        className={`drop-zone ${isDragging ? 'dragging' : ''} ${uploadError ? 'error' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="asset-photo-input"
          className="file-input"
          onChange={handleFileSelect}
          accept="image/*"
          disabled={isUploading}
        />
        <label htmlFor="asset-photo-input" className="drop-zone-label">
          {isUploading ? (
            <span className="loading">⏳ Загрузка...</span>
          ) : uploadError ? (
            <span className="error-text">❌ {uploadError}</span>
          ) : (
            <>
              <span className="icon">📸</span>
              <span className="text">Перетащите фото сюда или кликните для выбора</span>
              {allowedExtensions.length > 0 && (
                <span className="hint">Разрешенные форматы: {allowedExtensions.join(', ')}</span>
              )}
              <span className="hint">Максимальный размер: {maxSizeMB} MB</span>
            </>
          )}
        </label>
      </div>

      {showPreviews && error && (
        <div className="upload-error">
          <span>❌ {error}</span>
        </div>
      )}
    </div>
  );
};
