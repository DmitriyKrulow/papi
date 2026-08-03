// frontend/src/components/assets/AssetPhotoGallery.tsx
import { useState, useEffect, useCallback } from 'react';
import { X, ChevronLeft, ChevronRight, Trash2, Upload, Download } from 'lucide-react';
import { useAssetPhotos } from '../../hooks/useAssetPhotos';
import toast from 'react-hot-toast';

interface AssetPhotoGalleryProps {
  assetId: number;
  assetName?: string;
  isOpen: boolean;
  onClose: () => void;
}

interface PhotoGroup {
  label: string;
  category: string;
  photos: any[];
}

const PHOTO_CATEGORIES: Record<string, { label: string; stage: string }> = {
  general_view: { label: 'Общий вид', stage: 'receiving' },
  placement: { label: 'Место размещения', stage: 'receiving' },
  inventory_number: { label: 'Инвентарный номер', stage: 'receiving' },
  current_location: { label: 'Текущее местоположение', stage: 'inventory' },
  condition: { label: 'Состояние', stage: 'inventory' },
  malfunction: { label: 'Неисправность', stage: 'write_off' },
  general_condition: { label: 'Общее состояние', stage: 'write_off' },
};

const CATEGORY_ORDER = [
  'general_view', 'placement', 'inventory_number',
  'current_location', 'condition',
  'malfunction', 'general_condition',
];

const AssetPhotoGallery: React.FC<AssetPhotoGalleryProps> = ({
  assetId,
  assetName,
  isOpen,
  onClose,
}) => {
  const { photos, loading, fetchPhotos, uploadPhoto, deletePhoto } = useAssetPhotos(assetId);
  const [selectedPhoto, setSelectedPhoto] = useState<any>(null);
  const [selectedPhotoIndex, setSelectedPhotoIndex] = useState<number>(-1);
  const [uploadingCategory, setUploadingCategory] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchPhotos();
    }
  }, [isOpen, fetchPhotos]);

  // Группируем фотографии по категориям
  const photoGroups: PhotoGroup[] = CATEGORY_ORDER
    .filter(cat => PHOTO_CATEGORIES[cat])
    .map(cat => ({
      label: PHOTO_CATEGORIES[cat].label,
      category: cat,
      photos: photos.filter(p => p.photo_category === cat),
    }))
    .filter(group => group.photos.length > 0 || true); // показываем все группы

  // Фото без категории
  const uncategorizedPhotos = photos.filter(p => !p.photo_category || p.photo_category === 'other');

  const allPhotos = photos;
  const allPhotoIndices = Object.fromEntries(
    allPhotos.map((p, i) => [p.id, i])
  );

  const handlePhotoClick = (photo: any) => {
    setSelectedPhoto(photo);
    setSelectedPhotoIndex(allPhotoIndices[photo.id] ?? -1);
  };

  const handlePrevPhoto = () => {
    if (selectedPhotoIndex > 0) {
      setSelectedPhotoIndex(selectedPhotoIndex - 1);
      setSelectedPhoto(allPhotos[selectedPhotoIndex - 1]);
    }
  };

  const handleNextPhoto = () => {
    if (selectedPhotoIndex < allPhotos.length - 1) {
      setSelectedPhotoIndex(selectedPhotoIndex + 1);
      setSelectedPhoto(allPhotos[selectedPhotoIndex + 1]);
    }
  };

  const handleUpload = async (category: string, stage: string, file: File) => {
    setUploadingCategory(category);
    try {
      await uploadPhoto(file, {
        stage,
        photo_category: category,
        description: PHOTO_CATEGORIES[category]?.label || category,
        taken_at: new Date().toISOString(),
      });
      toast.success('Фото загружено');
    } catch (err) {
      toast.error('Ошибка загрузки фото');
    } finally {
      setUploadingCategory(null);
    }
  };

  const handleDelete = async (photoId: number) => {
    if (!confirm('Удалить фотографию?')) return;
    setDeletingId(photoId);
    try {
      await deletePhoto(photoId);
      if (selectedPhoto?.id === photoId) {
        setSelectedPhoto(null);
        setSelectedPhotoIndex(-1);
      }
      toast.success('Фото удалено');
    } catch {
      toast.error('Ошибка удаления фото');
    } finally {
      setDeletingId(null);
    }
  };

  const handleFileSelect = (category: string, stage: string, e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleUpload(category, stage, file);
    }
    e.target.value = '';
  };

  const getCategoryIcon = (category: string): string => {
    const icons: Record<string, string> = {
      general_view: '📷',
      placement: '📍',
      inventory_number: '🔢',
      current_location: '🗺️',
      condition: '🔍',
      malfunction: '⚠️',
      general_condition: '📋',
    };
    return icons[category] || '📸';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col m-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              Фотографии актива
            </h2>
            {assetName && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{assetName}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && photos.length === 0 ? (
            <div className="flex justify-center items-center py-16">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
              <span className="ml-3 text-gray-500">Загрузка фотографий...</span>
            </div>
          ) : (
            <div className="space-y-8">
              {/* Категории фото */}
              {CATEGORY_ORDER.map((cat) => {
                const catInfo = PHOTO_CATEGORIES[cat];
                if (!catInfo) return null;
                const groupPhotos = photos.filter(p => p.photo_category === cat);
                return (
                  <div key={cat} className="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider flex items-center gap-2">
                        <span>{getCategoryIcon(cat)}</span>
                        {catInfo.label}
                        <span className="text-xs text-gray-400 font-normal">({groupPhotos.length})</span>
                      </h3>
                      <label className="cursor-pointer">
                        <input
                          type="file"
                          accept="image/*"
                          className="hidden"
                          onChange={(e) => handleFileSelect(cat, catInfo.stage, e)}
                          disabled={uploadingCategory === cat}
                        />
                        <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition ${
                          uploadingCategory === cat
                            ? 'bg-blue-100 text-blue-400 cursor-wait'
                            : 'bg-blue-600 text-white hover:bg-blue-700 cursor-pointer'
                        }`}>
                          {uploadingCategory === cat ? (
                            <>⏳ Загрузка...</>
                          ) : (
                            <><Upload className="w-3.5 h-3.5" /> Добавить</>
                          )}
                        </span>
                      </label>
                    </div>

                    {groupPhotos.length === 0 ? (
                      <p className="text-sm text-gray-400 dark:text-gray-500 italic pl-1">
                        Нет фотографий. Нажмите «Добавить», чтобы загрузить.
                      </p>
                    ) : (
                      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                        {groupPhotos.map((photo) => (
                          <div
                            key={photo.id}
                            className="relative group aspect-square rounded-lg overflow-hidden bg-gray-200 dark:bg-gray-700 cursor-pointer border border-gray-200 dark:border-gray-600"
                            onClick={() => handlePhotoClick(photo)}
                          >
                            <img
                              src={`/api/asset-photos/${photo.id}/download`}
                              alt={photo.description || 'Фото актива'}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23999"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>';
                              }}
                            />
                            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition flex items-center justify-center gap-2">
                              <button
                                onClick={(e) => { e.stopPropagation(); handlePhotoClick(photo); }}
                                className="opacity-0 group-hover:opacity-100 p-1.5 bg-white/90 rounded-lg hover:bg-white transition"
                                title="Просмотреть"
                              >
                                <Download className="w-4 h-4 text-gray-700" />
                              </button>
                              <button
                                onClick={(e) => { e.stopPropagation(); handleDelete(photo.id); }}
                                disabled={deletingId === photo.id}
                                className="opacity-0 group-hover:opacity-100 p-1.5 bg-white/90 rounded-lg hover:bg-red-50 transition"
                                title="Удалить"
                              >
                                <Trash2 className="w-4 h-4 text-red-500" />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}

              {/* Фото без категории */}
              {uncategorizedPhotos.length > 0 && (
                <div className="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-4">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <span>📸</span>
                    Другие фотографии
                    <span className="text-xs text-gray-400 font-normal">({uncategorizedPhotos.length})</span>
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                    {uncategorizedPhotos.map((photo) => (
                      <div
                        key={photo.id}
                        className="relative group aspect-square rounded-lg overflow-hidden bg-gray-200 dark:bg-gray-700 cursor-pointer border border-gray-200 dark:border-gray-600"
                        onClick={() => handlePhotoClick(photo)}
                      >
                        <img
                          src={`/api/asset-photos/${photo.id}/download`}
                          alt={photo.description || 'Фото'}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23999"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>';
                          }}
                        />
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition flex items-center justify-center gap-2">
                          <button
                            onClick={(e) => { e.stopPropagation(); handlePhotoClick(photo); }}
                            className="opacity-0 group-hover:opacity-100 p-1.5 bg-white/90 rounded-lg hover:bg-white transition"
                          >
                            <Download className="w-4 h-4 text-gray-700" />
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleDelete(photo.id); }}
                            disabled={deletingId === photo.id}
                            className="opacity-0 group-hover:opacity-100 p-1.5 bg-white/90 rounded-lg hover:bg-red-50 transition"
                          >
                            <Trash2 className="w-4 h-4 text-red-500" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {photos.length === 0 && (
                <div className="text-center py-16">
                  <div className="text-6xl mb-4">📷</div>
                  <p className="text-gray-500 dark:text-gray-400 mb-2">
                    Нет фотографий для этого актива
                  </p>
                  <p className="text-sm text-gray-400 dark:text-gray-500">
                    Загрузите фотографии, используя кнопки «Добавить» в каждой категории выше
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Photo Viewer Modal */}
      {selectedPhoto && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80"
          onClick={() => setSelectedPhoto(null)}
        >
          <div
            className="relative max-w-4xl max-h-[90vh] m-4"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setSelectedPhoto(null)}
              className="absolute -top-10 right-0 text-white/70 hover:text-white transition"
            >
              <X className="w-6 h-6" />
            </button>

            {/* Navigation arrows */}
            {selectedPhotoIndex > 0 && (
              <button
                onClick={handlePrevPhoto}
                className="absolute left-2 top-1/2 -translate-y-1/2 p-2 bg-black/40 hover:bg-black/60 text-white rounded-full transition"
              >
                <ChevronLeft className="w-6 h-6" />
              </button>
            )}
            {selectedPhotoIndex < allPhotos.length - 1 && (
              <button
                onClick={handleNextPhoto}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-black/40 hover:bg-black/60 text-white rounded-full transition"
              >
                <ChevronRight className="w-6 h-6" />
              </button>
            )}

            <img
              src={`/api/asset-photos/${selectedPhoto.id}/download`}
              alt={selectedPhoto.description || 'Фото актива'}
              className="max-w-full max-h-[85vh] rounded-lg object-contain"
            />

            <div className="absolute -bottom-10 left-0 right-0 flex items-center justify-between text-white/70 text-sm">
              <div className="flex items-center gap-3">
                <span>
                  {selectedPhoto.photo_category && PHOTO_CATEGORIES[selectedPhoto.photo_category]
                    ? PHOTO_CATEGORIES[selectedPhoto.photo_category].label
                    : selectedPhoto.stage}
                </span>
                {selectedPhoto.description && (
                  <span className="text-white/50">— {selectedPhoto.description}</span>
                )}
              </div>
              <span>
                {selectedPhotoIndex + 1} / {allPhotos.length}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AssetPhotoGallery;