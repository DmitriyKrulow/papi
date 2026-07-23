import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAssets } from '../hooks/useAssets';

const AssetDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { assets, loading, error } = useAssets();
  const [asset, setAsset] = useState<any>(null);

  useEffect(() => {
    if (!loading && assets.length > 0) {
      const found = assets.find((a) => a.id === parseInt(id || '0'));
      if (found) {
        setAsset(found);
      } else {
        navigate('/assets');
      }
    }
  }, [assets, loading, id, navigate]);

  if (loading) return <div>Загрузка...</div>;
  if (error) return <div className="text-red-500">Ошибка: {error}</div>;
  if (!asset) return <div>Актив не найден</div>;

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <button
        onClick={() => navigate('/assets')}
        className="mb-4 text-blue-600 hover:text-blue-800"
      >
        ← Назад к списку
      </button>

      <h1 className="text-3xl font-bold text-gray-900 mb-6">Детали актива</h1>

      <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg leading-6 font-medium text-gray-900">{asset.name}</h3>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                Инвентарный номер: {asset.inventory_number}
              </p>
            </div>
            <div>
              <span
                className={`inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium ${
                  asset.status === 'active'
                    ? 'bg-green-100 text-green-800'
                    : asset.status === 'written_off'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-yellow-100 text-yellow-800'
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
              <dt className="text-sm font-medium text-gray-500">Модель</dt>
              <dd className="mt-1 text-sm text-gray-900">{asset.model || 'Не указано'}</dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Производитель</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {asset.manufacturer_name || 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Страна</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {asset.country_of_origin || 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Цена покупки</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {asset.purchase_price
                  ? new Intl.NumberFormat('ru-RU', {
                      style: 'currency',
                      currency: 'RUB',
                    }).format(Number(asset.purchase_price))
                  : 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Текущая стоимость</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {asset.current_value
                  ? new Intl.NumberFormat('ru-RU', {
                      style: 'currency',
                      currency: 'RUB',
                    }).format(Number(asset.current_value))
                  : 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Ставка амортизации</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {asset.depreciation_rate ? `${asset.depreciation_rate}%` : 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Подразделение</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {asset.department_code || 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Ответственный</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {asset.responsible_person || 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Телефон</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {asset.responsible_phone || 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Адрес</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {asset.location_address || 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Дата покупки</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {asset.purchase_date
                  ? new Date(asset.purchase_date).toLocaleDateString('ru-RU')
                  : 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Дата ввода в эксплуатацию</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {asset.commissioning_date
                  ? new Date(asset.commissioning_date).toLocaleDateString('ru-RU')
                  : 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Гарантия</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {asset.warranty_expiry
                  ? new Date(asset.warranty_expiry).toLocaleDateString('ru-RU')
                  : 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Последнее ТО</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {asset.last_maintenance_date
                  ? new Date(asset.last_maintenance_date).toLocaleDateString('ru-RU')
                  : 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Списание</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {asset.decommissioning_date
                  ? new Date(asset.decommissioning_date).toLocaleDateString('ru-RU')
                  : 'Не указано'}
              </dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-sm font-medium text-gray-500">Описание</dt>
              <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                {asset.description || 'Нет описания'}
              </dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-sm font-medium text-gray-500">Примечания</dt>
              <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                {asset.notes || 'Нет примечаний'}
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
};

export default AssetDetail;
