// frontend/src/pages/InventoryAssetMobile.tsx
import { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  ArrowLeft, CheckCircle2, XCircle, Loader2, Camera
} from 'lucide-react';
import toast from 'react-hot-toast';

interface Asset {
  id: number;
  inventory_number: string;
  name: string;
  status?: string;
  responsible_person?: string;
  purchase_date?: string;
  location_address?: string;
  last_inventory_date?: string;
  last_inventory_confirmed?: boolean;
  asset_photos?: Array<{
    id: number;
    photo_url: string;
    photo_category: string;
    uploaded_at: string;
  }>;
}

interface InventoryCheck {
  id: number;
  name: string;
  check_type: string;
  started_at: string;
  found: number;
  missing: number;
  total_checked: number;
}

const InventoryAssetMobile: React.FC = () => {
  const navigate = useNavigate();
  const { getToken, user } = useAuth();
  const [searchParams] = useSearchParams();
  
  const checkId = parseInt(searchParams.get('check_id') || '0');
  const assetId = parseInt(window.location.pathname.split('/').pop() || '0');
  
  const [asset, setAsset] = useState<Asset | null>(null);
  const [inventory, setInventory] = useState<InventoryCheck | null>(null);
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const [confirmResult, setConfirmResult] = useState<'found' | 'missing' | null>(null);
  const [newPhoto, setNewPhoto] = useState<string | null>(null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchData();
  }, [assetId, checkId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      
      // Получаем данные актива
      const assetRes = await fetch(`/api/assets/${assetId}`, {
        headers: { 'Authorization': token ? `Bearer ${token}` : '' },
      });
      
      if (assetRes.ok) {
        const assetData = await assetRes.json();
        setAsset(assetData);
      } else {
        toast.error('Актив не найден');
      }
      
      // Получаем активную инвентаризацию
      const invRes = await fetch('/api/inventory-checks/active', {
        headers: { 'Authorization': token ? `Bearer ${token}` : '' },
      });
      
      if (invRes.ok) {
        const invData = await invRes.json();
        if (invData && invData.id === checkId) {
          setInventory(invData);
        }
      }
    } catch (err) {
      toast.error('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (found: boolean) => {
    if (!inventory || !asset) return;
    
    try {
      setConfirming(true);
      const token = await getToken();
      
      const res = await fetch(
        `/api/inventory-checks/${inventory.id}/confirm/${asset.id}?found=${found}`,
        {
          method: 'POST',
          headers: {
            'Authorization': token ? `Bearer ${token}` : '',
            'Content-Type': 'application/json',
          },
        }
      );

      if (res.ok) {
        const data = await res.json();
        setConfirmResult(found ? 'found' : 'missing');
        toast.success(data.message);
        
        // Обновляем данные актива
        const updatedAssetRes = await fetch(`/api/assets/${assetId}`, {
          headers: { 'Authorization': token ? `Bearer ${token}` : '' },
        });
        if (updatedAssetRes.ok) {
          setAsset(await updatedAssetRes.json());
        }
        
        // Обновляем данные инвентаризации
        const updatedInvRes = await fetch('/api/inventory-checks/active', {
          headers: { 'Authorization': token ? `Bearer ${token}` : '' },
        });
        if (updatedInvRes.ok) {
          setInventory(await updatedInvRes.json());
        }
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Ошибка подтверждения');
      }
    } catch (err) {
      toast.error('Ошибка соединения');
    } finally {
      setConfirming(false);
      setTimeout(() => setConfirmResult(null), 3000);
    }
  };

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setNewPhoto(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUploadPhoto = async () => {
    if (!newPhoto || !asset) return;
    
    try {
      setUploadingPhoto(true);
      const token = await getToken();
      
      // Отправляем фото на сервер
      const formData = new FormData();
      const response = await fetch(newPhoto);
      const blob = await response.blob();
      formData.append('photo', blob, `${asset.inventory_number}_${Date.now()}.jpg`);
      formData.append('category', 'inventory');
      formData.append('description', `Фото инвентаризации ${new Date().toLocaleDateString('ru-RU')}`);
      
      const uploadRes = await fetch(`/api/assets/${assetId}/photos`, {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
        body: formData,
      });
      
      if (uploadRes.ok) {
        toast.success('Фото загружено');
        setNewPhoto(null);
        // Обновляем список фото
        const updatedAssetRes = await fetch(`/api/assets/${assetId}`, {
          headers: { 'Authorization': token ? `Bearer ${token}` : '' },
        });
        if (updatedAssetRes.ok) {
          setAsset(await updatedAssetRes.json());
        }
      } else {
        toast.error('Ошибка загрузки фото');
      }
    } catch (err) {
      toast.error('Ошибка соединения');
    } finally {
      setUploadingPhoto(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-blue-600 dark:text-blue-400 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">Загрузка данных...</p>
        </div>
      </div>
    );
  }

  if (!asset) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center p-4">
          <XCircle className="w-12 h-12 text-red-600 dark:text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Актив не найден
          </h2>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            Возможно, актив был удален или не существует
          </p>
          <button
            onClick={() => navigate('/inventory-mobile')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Вернуться к инвентаризации
          </button>
        </div>
      </div>
    );
  }

  const isConfirmed = asset.last_inventory_confirmed;
  const isInInventory = inventory && assetId > 0;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10">
        <div className="flex items-center justify-between p-4">
          <button
            onClick={() => navigate('/inventory-mobile')}
            className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="font-medium">Назад</span>
          </button>
          {isConfirmed && (
            <div className="flex items-center gap-1 px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-sm">
              <CheckCircle2 className="w-4 h-4" />
              <span>Проверен</span>
            </div>
          )}
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Inventory Info */}
        {isInInventory && inventory && (
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
            <div className="flex items-center gap-2 mb-2">
              <Loader2 className="w-5 h-5 text-blue-600 dark:text-blue-400 animate-spin" />
              <h2 className="text-lg font-bold text-blue-900 dark:text-blue-100">
                {inventory.name}
              </h2>
            </div>
            <div className="flex justify-between text-sm text-blue-700 dark:text-blue-300">
              <span>Найдено: {inventory.found}</span>
              <span>Отсутствует: {inventory.missing}</span>
              <span>Осталось: {inventory.total_checked - inventory.found - inventory.missing}</span>
            </div>
          </div>
        )}

        {/* Asset Info — минимум как на маркировке */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 border border-gray-200 dark:border-gray-700">
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-3">
            {asset.name}
          </h1>
          
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-gray-500 dark:text-gray-400 w-28 shrink-0">Инв. №:</span>
              <span className="font-mono font-medium text-gray-900 dark:text-gray-100">
                {asset.inventory_number}
              </span>
            </div>
            
            <div className="flex items-center gap-2">
              <span className="text-gray-500 dark:text-gray-400 w-28 shrink-0">Статус:</span>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                asset.status === 'in_use' 
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                  : asset.status === 'retired'
                  ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}>
                {asset.status === 'in_use' ? 'В использовании' : 
                 asset.status === 'retired' ? 'Списан' :
                 asset.status === 'in_storage' ? 'На складе' :
                 asset.status || '—'}
              </span>
            </div>
            
            {asset.responsible_person && (
              <div className="flex items-center gap-2">
                <span className="text-gray-500 dark:text-gray-400 w-28 shrink-0">Ответственный:</span>
                <span className="text-gray-900 dark:text-gray-100">{asset.responsible_person}</span>
              </div>
            )}
            
            {asset.location_address && (
              <div className="flex items-center gap-2">
                <span className="text-gray-500 dark:text-gray-400 w-28 shrink-0">Местоположение:</span>
                <span className="text-gray-900 dark:text-gray-100">{asset.location_address}</span>
              </div>
            )}
            
            {asset.purchase_date && (
              <div className="flex items-center gap-2">
                <span className="text-gray-500 dark:text-gray-400 w-28 shrink-0">Пост. на учёт:</span>
                <span className="text-gray-900 dark:text-gray-100">
                  {new Date(asset.purchase_date).toLocaleDateString('ru-RU')}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Photos */}
        {asset.asset_photos && asset.asset_photos.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 border border-gray-200 dark:border-gray-700">
            <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-3">
              Фотографии ({asset.asset_photos.length})
            </h2>
            <div className="grid grid-cols-2 gap-2">
              {asset.asset_photos.map((photo) => (
                <div key={photo.id} className="relative group">
                  <img
                    src={photo.photo_url}
                    alt="Фото актива"
                    className="w-full h-32 object-cover rounded-lg"
                  />
                  <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition rounded-lg flex items-center justify-center">
                    <span className="text-white text-xs opacity-0 group-hover:opacity-100">
                      {new Date(photo.uploaded_at).toLocaleDateString('ru-RU')}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Upload New Photo */}
        {isInInventory && !isConfirmed && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 border border-gray-200 dark:border-gray-700">
            <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
              <Camera className="w-5 h-5" />
              Добавить фото
            </h2>
            
            {newPhoto ? (
              <div className="space-y-3">
                <img
                  src={newPhoto}
                  alt="Предпросмотр"
                  className="w-full h-48 object-cover rounded-lg"
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => setNewPhoto(null)}
                    className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition text-gray-700 dark:text-gray-300"
                  >
                    Отмена
                  </button>
                  <button
                    onClick={handleUploadPhoto}
                    disabled={uploadingPhoto}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition disabled:opacity-50"
                  >
                    {uploadingPhoto ? (
                      <span className="flex items-center justify-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Загрузка...
                      </span>
                    ) : (
                      'Загрузить'
                    )}
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full px-4 py-3 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg text-sm hover:border-blue-500 dark:hover:border-blue-400 transition text-gray-600 dark:text-gray-400"
              >
                <Camera className="w-6 h-6 mx-auto mb-2" />
                <span>Сделать фото или выбрать файл</span>
              </button>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handlePhotoUpload}
              className="hidden"
            />
          </div>
        )}

        {/* Confirm Actions */}
        {isInInventory && !isConfirmed && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 border border-gray-200 dark:border-gray-700">
            <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-3">
              Подтвердить наличие
            </h2>
            
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => handleConfirm(true)}
                disabled={confirming}
                className="px-4 py-3 bg-green-600 dark:bg-green-700 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-600 transition disabled:opacity-50 font-medium flex items-center justify-center gap-2"
              >
                {confirming && confirmResult === 'found' ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <CheckCircle2 className="w-5 h-5" />
                )}
                Найден
              </button>
              
              <button
                onClick={() => handleConfirm(false)}
                disabled={confirming}
                className="px-4 py-3 bg-red-600 dark:bg-red-700 text-white rounded-lg hover:bg-red-700 dark:hover:bg-red-600 transition disabled:opacity-50 font-medium flex items-center justify-center gap-2"
              >
                {confirming && confirmResult === 'missing' ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <XCircle className="w-5 h-5" />
                )}
                Отсутствует
              </button>
            </div>
          </div>
        )}

        {/* Already Confirmed */}
        {isConfirmed && (
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
            <div className="flex items-center gap-2 text-green-700 dark:text-green-300">
              <CheckCircle2 className="w-6 h-6" />
              <div>
                <h3 className="font-semibold">Актив проверен</h3>
                <p className="text-sm">
                  {asset.last_inventory_date && (
                    <span>
                      Проверен: {new Date(asset.last_inventory_date).toLocaleDateString('ru-RU')}
                    </span>
                  )}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default InventoryAssetMobile;
