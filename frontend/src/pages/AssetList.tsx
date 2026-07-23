import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAssets } from '../hooks/useAssets';
import { useAuth } from '../hooks/useAuth';
import { UserRole } from '../domain/roles';

const AssetList: React.FC = () => {
  const { assets, loading, error, deleteAsset } = useAssets();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');

  const filteredAssets = assets.filter((asset) =>
    asset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    asset.inventory_number.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleDelete = async (id: number) => {
    if (window.confirm('Вы уверены, что хотите удалить этот актив?')) {
      try {
        await deleteAsset(id);
      } catch (err) {
        console.error('Failed to delete asset:', err);
      }
    }
  };

  if (loading) return <div>Загрузка...</div>;
  if (error) return <div className="text-red-500">Ошибка: {error}</div>;

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Список активов</h1>
        {user?.role === UserRole.ADMIN && (
          <button
            onClick={() => navigate('/assets/create')}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Добавить актив
          </button>
        )}
      </div>

      <div className="mb-4">
        <input
          type="text"
          placeholder="Поиск..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        {filteredAssets.length > 0 ? (
          <ul className="divide-y divide-gray-200">
            {filteredAssets.map((asset) => (
              <li key={asset.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-blue-600 truncate">
                      <Link to={`/assets/${asset.id}`} className="hover:underline">
                        {asset.name}
                      </Link>
                    </p>
                    <div className="mt-1 flex items-center text-sm text-gray-500">
                      <span className="mr-2">Инв. № {asset.inventory_number}</span>
                      <span className="mx-2">•</span>
                      <span>{asset.department_code || 'Без подразделения'}</span>
                    </div>
                  </div>
                  <div className="ml-2 flex-shrink-0 flex">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
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
                <div className="mt-2 flex items-center justify-between">
                  <div className="text-sm text-gray-500">
                    {asset.current_value
                      ? new Intl.NumberFormat('ru-RU', {
                          style: 'currency',
                          currency: 'RUB',
                        }).format(Number(asset.current_value))
                      : 'Цена не указана'}
                  </div>
                  {user?.role === UserRole.ADMIN && (
                    <div className="flex space-x-2">
                      <Link
                        to={`/assets/${asset.id}/edit`}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Редактировать
                      </Link>
                      <button
                        onClick={() => handleDelete(asset.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Удалить
                      </button>
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="px-4 py-5 sm:p-6 text-center text-gray-500">
            {searchTerm ? 'Ничего не найдено' : 'Список активов пуст'}
          </div>
        )}
      </div>
    </div>
  );
};

export default AssetList;
