import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Image } from 'lucide-react';
import AssetPhotoGallery from '../components/assets/AssetPhotoGallery';

const AssetDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [asset, setAsset] = useState<any>(null);
  const [assetLoading, setAssetLoading] = useState(true);
  const [assetError, setAssetError] = useState<string | null>(null);
  const [isGalleryOpen, setIsGalleryOpen] = useState(false);

  const loadAsset = useCallback(async () => {
    if (!id) return;
    
    setAssetLoading(true);
    setAssetError(null);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setAssetError('Токен авторизации не найден');
        return;
      }
      
      const response = await fetch(`/api/assets/${id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        if (response.status === 404) {
          setAssetError('Актив не найден');
        } else if (response.status === 401 || response.status === 403) {
          setAssetError('Сессия истекла. Пожалуйста, войдите снова.');
        } else {
          setAssetError(`Ошибка загрузки: ${response.status}`);
        }
        return;
      }
      
      const data = await response.json();
      setAsset(data);
    } catch (err) {
      console.error('[AssetDetail] Failed to load asset:', err);
      setAssetError('Не удалось загрузить актив');
    } finally {
      setAssetLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadAsset();
  }, [loadAsset]);

  if (assetLoading) return <div className="p-8 text-center">Загрузка...</div>;
  if (assetError) {
    return (
      <div className="p-8 text-center">
        <div className="text-red-500 dark:text-red-400 mb-4">{assetError}</div>
        <button
          onClick={() => navigate('/assets')}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          ← Назад к списку
        </button>
      </div>
    );
  }
  if (!asset) return <div className="p-8 text-center">Актив не найден</div>;

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <button
        onClick={() => navigate('/assets')}
        className="mb-4 text-blue-600 hover:text-blue-800"
      >
        ← Назад к списку
      </button>

      <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">Детали актива</h1>

      <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg mb-6">
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-gray-100">{asset.name}</h3>
              <p className="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">
                Инвентарный номер: {asset.inventory_number}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setIsGalleryOpen(true)}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition"
              >
                <Image className="w-4 h-4" />
                Фотографии
              </button>
              <span
                className={`inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium ${
                  asset.status === 'active'
                    ? 'bg-green-100 text-green-800 dark:text-green-200'
                    : asset.status === 'written_off'
                    ? 'bg-red-100 text-red-800 dark:text-red-200'
                    : 'bg-yellow-100 text-yellow-800 dark:text-yellow-200'
                }`}
              >
                {asset.status}
              </span>
            </div>
          </div>
        </div>

        <div className="px-4 py-5 sm:p-6">
          <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Модель</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">{asset.model || 'Не указано'}</dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Производитель</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                {asset.manufacturer_name || 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Страна</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                {asset.country_of_origin || 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Цена покупки</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                {asset.purchase_price
                  ? new Intl.NumberFormat('ru-RU', {
                      style: 'currency',
                      currency: 'RUB',
                    }).format(Number(asset.purchase_price))
                  : 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Текущая стоимость</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                {asset.current_value
                  ? new Intl.NumberFormat('ru-RU', {
                      style: 'currency',
                      currency: 'RUB',
                    }).format(Number(asset.current_value))
                  : 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Ставка амортизации</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                {asset.depreciation_rate ? `${asset.depreciation_rate}%` : 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Подразделение</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                {asset.department_code || 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Ответственный</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                {asset.responsible_person || 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Телефон</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                {asset.responsible_phone || 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Адрес</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                {asset.location_address || asset.storage_address_name || 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Дата покупки</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                {asset.purchase_date
                  ? new Date(asset.purchase_date).toLocaleDateString('ru-RU')
                  : 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Дата ввода в эксплуатацию</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                {asset.commissioning_date
                  ? new Date(asset.commissioning_date).toLocaleDateString('ru-RU')
                  : 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Гарантия</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                {asset.warranty_expiry
                  ? new Date(asset.warranty_expiry).toLocaleDateString('ru-RU')
                  : 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Последнее ТО</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                {asset.last_maintenance_date
                  ? new Date(asset.last_maintenance_date).toLocaleDateString('ru-RU')
                  : 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Списание</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                {asset.decommissioning_date
                  ? new Date(asset.decommissioning_date).toLocaleDateString('ru-RU')
                  : 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Описание</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100 whitespace-pre-wrap">
                {asset.description || 'Нет описания'}
              </dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Примечания</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100 whitespace-pre-wrap">
                {asset.notes || 'Нет примечаний'}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      {/* Photo Gallery Modal */}
      <AssetPhotoGallery
        assetId={parseInt(id || '0')}
        assetName={asset.name}
        isOpen={isGalleryOpen}
        onClose={() => setIsGalleryOpen(false)}
      />
    </div>
  );
};

export default AssetDetail;
