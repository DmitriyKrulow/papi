// frontend/src/components/assets/AssetPhotoList.tsx
import { useState } from 'react';
import { useAssetPhotos } from '../../hooks/useAssetPhotos';

interface AssetPhotoListProps {
  assetId: number;
  assetName?: string;
}

export const AssetPhotoList = ({ assetId, assetName }: AssetPhotoListProps) => {
  const { photos, loading, deletePhoto, error } = useAssetPhotos(assetId);
  const [deletingId, setDeletingId] = useState<number | null>(null);

const getStageLabel = (stage: string) => {
    const labels: Record<string, string> = {
      receiving: 'При поступлении',
      inventory: 'При инвентаризации',
      write_off: 'Перед списанием',
      repair: 'Во время ремонта',
      maintenance: 'Во время ТО',
      movement: 'При перемещении',
      other: 'Другое',
    };
    return labels[stage] || stage;
  };

  const getCategoryLabel = (category: string | undefined) => {
    const labels: Record<string, string> = {
      general_view: 'Общий вид',
      placement: 'Место размещения',
      inventory_number: 'Инвентарный номер',
      current_location: 'Текущее местоположение',
      condition: 'Состояние',
      malfunction: 'Неисправность',
      general_condition: 'Общее состояние',
    };
    return category ? labels[category] || category : '';
  };

  const handleDelete = async (photoId: number) => {
    if (!confirm('Удалить фотографию?')) return;

    setDeletingId(photoId);
    try {
      await deletePhoto(photoId);
    } finally {
      setDeletingId(null);
    }
  };

  if (loading && photos.length === 0) {
    return <div className="loading-photos">Загрузка фотографий...</div>;
  }

  return (
    <div className="asset-photo-list">
      <h3>
        Фотографии актива{assetName && ` "${assetName}"`}
        {photos.length > 0 && ` (${photos.length})`}
      </h3>
      
      {error && <div className="error">{error}</div>}
      
      {photos.length === 0 ? (
        <div className="no-photos">
          <span className="icon">📷</span>
          <span>Нет фотографий актива</span>
          <span className="hint">Загрузите фото с помощью формы выше</span>
        </div>
      ) : (
        <div className="photos-grid">
          {photos.map((photo) => (
            <div key={photo.id} className="photo-card">
              <div className="photo-image">
<img
                  src={`/api/asset-photos/${photo.id}/download`}
                  alt={`Фото актива ${photo.id}`}
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23999"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>';
                  }}
                />
                <div className="photo-overlay">
                  <button
                    className="delete-btn"
                    onClick={() => handleDelete(photo.id)}
                    disabled={deletingId === photo.id}
                  >
                    🗑️
                  </button>
                </div>
              </div>
<div className="photo-info">
                  <div className="photo-meta">
                    <span className="stage">{getStageLabel(photo.stage)}</span>
                    {photo.photo_category && <span className="category">{getCategoryLabel(photo.photo_category)}</span>}
                    {photo.description && <span className="description">{photo.description}</span>}
                  {photo.is_before && <span className="badge badge-before">До</span>}
                  {photo.is_after && <span className="badge badge-after">После</span>}
                  {photo.inventory_check_id && (
                    <span className="badge badge-inventory">Инвентаризация #{photo.inventory_check_id}</span>
                  )}
                  {photo.repair_request_id && (
                    <span className="badge badge-repair">Ремонт #{photo.repair_request_id}</span>
                  )}
                </div>
                <div className="photo-date">
                  {new Date(photo.uploaded_at).toLocaleDateString('ru-RU')}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};