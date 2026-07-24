// frontend/src/pages/Assets.tsx
import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
// Удаляем неиспользуемый импорт
// import { apiClient } from '../api/client';
import type { Asset } from '../types';
import { AssetStatusMap } from '../types';
import { formatMoney } from '../utils/helpers';
import toast from 'react-hot-toast';
import AssetModal from '../components/assets/AssetModal';
import AddAssetForm from '../components/assets/AddAssetForm';
import EditAssetForm from '../components/assets/EditAssetForm';
import AssetDetailsModal from '../components/assets/AssetDetailsModal';

const Assets: React.FC = () => {
  const navigate = useNavigate();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortField, setSortField] = useState<keyof Asset>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [itemsPerPage, setItemsPerPage] = useState<number>(10);
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState<boolean>(false);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState<boolean>(false);
  const [currentAsset, setCurrentAsset] = useState<Asset | null>(null);

  useEffect(() => {
    const fetchAssets = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('token');
        const response = await fetch('/api/assets', {
          headers: {
            'Authorization': token ? `Bearer ${token}` : '',
          },
        });
        
        if (response.ok) {
          const data = await response.json();
          setAssets(data.items || data || []);
          setError(null);
        } else {
          setError('Ошибка загрузки активов');
          toast.error('Ошибка загрузки активов');
        }
      } catch (err: any) {
        setError('Ошибка загрузки активов: ' + (err.message || 'Неизвестная ошибка'));
        toast.error('Ошибка загрузки активов');
      } finally {
        setLoading(false);
      }
    };

    fetchAssets();
  }, []);

  const filteredAssets = useMemo(() => {
    return assets.filter((asset) => {
      const matchesSearch =
        asset.inventory_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        asset.name?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus = statusFilter === 'all' || asset.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [assets, searchQuery, statusFilter]);

  const sortedAssets = useMemo(() => {
    return [...filteredAssets].sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];

      if (aValue === undefined && bValue === undefined) return 0;
      if (aValue === undefined) return 1;
      if (bValue === undefined) return -1;

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
      }

      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filteredAssets, sortField, sortOrder]);

  const totalPages = Math.ceil(sortedAssets.length / itemsPerPage);
  const paginatedAssets = sortedAssets.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setCurrentPage(1);
  };

  const handleStatusFilter = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value);
    setCurrentPage(1);
  };

  const handleSort = (field: keyof Asset) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };

  const handleAddAsset = async (asset: Omit<Asset, 'id' | 'created_at' | 'updated_at'>) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/assets', {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(asset),
      });
      
      if (response.ok) {
        const newAsset = await response.json();
        setAssets((prev) => [...prev, newAsset]);
        toast.success('Актив добавлен');
        setIsAddModalOpen(false);
      } else {
        toast.error('Ошибка добавления актива');
      }
    } catch (err: any) {
      toast.error('Ошибка добавления актива');
    }
  };

  const handleEditAsset = async (asset: Asset) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/assets/${asset.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(asset),
      });
      
      if (response.ok) {
        const updatedAsset = await response.json();
        setAssets((prev) =>
          prev.map((a) => (a.id === asset.id ? updatedAsset : a))
        );
        toast.success('Актив обновлен');
        setIsEditModalOpen(false);
        setCurrentAsset(null);
      } else {
        toast.error('Ошибка обновления актива');
      }
    } catch (err: any) {
      toast.error('Ошибка обновления актива');
    }
  };

  const handleDeleteAsset = async (id: number) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот актив?')) return;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/assets/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });
      
      if (response.ok) {
        setAssets((prev) => prev.filter((a) => a.id !== id));
        toast.success('Актив удален');
      } else {
        toast.error('Ошибка удаления актива');
      }
    } catch (err: any) {
      toast.error('Ошибка удаления актива');
    }
  };

  const handleViewDetails = (asset: Asset) => {
    setCurrentAsset(asset);
    setIsDetailsModalOpen(true);
  };

  const handleEditClick = (asset: Asset) => {
    setCurrentAsset(asset);
    setIsEditModalOpen(true);
  };

  const getStatusBadge = (status: string) => {
    const statusInfo = AssetStatusMap[status as keyof typeof AssetStatusMap];
    const colors: Record<string, string> = {
      green: 'bg-green-100 text-green-700',
      yellow: 'bg-yellow-100 text-yellow-700',
      blue: 'bg-blue-100 text-blue-700',
      gray: 'bg-gray-100 text-gray-700',
      red: 'bg-red-100 text-red-700',
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[statusInfo?.color || 'gray']}`}>
        {statusInfo?.label || status}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="text-gray-500">⏳ Загрузка активов...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">
        <strong>❌ Ошибка:</strong> {error}
      </div>
    );
  }

  return (
    <div>
      <div className="flex flex-wrap justify-between items-center gap-4 mb-6">
        <h1 className="text-2xl font-bold text-gray-800">📦 Активы</h1>
        <div className="flex gap-2">
          <button
            onClick={() => navigate('/assets/create')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition flex items-center gap-2"
          >
            <span>➕</span> Добавить актив
          </button>
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition flex items-center gap-2"
          >
            <span>📤</span> Быстрое добавление
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-4 mb-6 space-y-4">
        <div className="flex flex-wrap gap-4">
          <input
            type="text"
            placeholder="Поиск по инвентарному номеру или названию..."
            value={searchQuery}
            onChange={handleSearch}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <select
            value={statusFilter}
            onChange={handleStatusFilter}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">Все статусы</option>
            {Object.keys(AssetStatusMap).map((status) => (
              <option key={status} value={status}>
                {AssetStatusMap[status as keyof typeof AssetStatusMap].label}
              </option>
            ))}
          </select>
          <select
            value={itemsPerPage}
            onChange={(e) => {
              setItemsPerPage(Number(e.target.value));
              setCurrentPage(1);
            }}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value={10}>10 шт.</option>
            <option value={20}>20 шт.</option>
            <option value={50}>50 шт.</option>
          </select>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        {paginatedAssets.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">📭</div>
            <p className="text-gray-500">Нет активов для отображения</p>
            <p className="text-gray-400 text-sm mt-1">
              {searchQuery || statusFilter !== 'all'
                ? 'Попробуйте изменить фильтры поиска'
                : 'Добавьте первый актив, нажав кнопку выше'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100 transition"
                    onClick={() => handleSort('inventory_number')}
                  >
                    Инв. номер {sortField === 'inventory_number' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100 transition"
                    onClick={() => handleSort('name')}
                  >
                    Название {sortField === 'name' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100 transition"
                    onClick={() => handleSort('current_value')}
                  >
                    Стоимость {sortField === 'current_value' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100 transition"
                    onClick={() => handleSort('status')}
                  >
                    Статус {sortField === 'status' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Действия
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {paginatedAssets.map((asset) => (
                  <tr key={asset.id} className="hover:bg-gray-50 transition">
                    <td className="px-6 py-4 text-sm font-mono text-gray-900">
                      {asset.inventory_number}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {asset.name}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {formatMoney(asset.current_value)}
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(asset.status)}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <button
                        onClick={() => handleViewDetails(asset)}
                        className="text-blue-600 hover:text-blue-800 mr-3 transition"
                        title="Просмотреть"
                      >
                        👁️
                      </button>
                      <button
                        onClick={() => handleEditClick(asset)}
                        className="text-green-600 hover:text-green-800 mr-3 transition"
                        title="Редактировать"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => handleDeleteAsset(asset.id)}
                        className="text-red-600 hover:text-red-800 transition"
                        title="Удалить"
                      >
                        🗑️
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <div className="px-6 py-4 border-t flex items-center justify-between">
            <span className="text-sm text-gray-500">
              Показано {paginatedAssets.length} из {sortedAssets.length} активов
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ← Назад
              </button>
              <span className="px-3 py-1">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Вперед →
              </button>
            </div>
          </div>
        )}
      </div>

      <AssetModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Добавить актив"
      >
        <AddAssetForm
          onSubmit={handleAddAsset}
          onClose={() => setIsAddModalOpen(false)}
        />
      </AssetModal>

      {currentAsset && (
        <>
          <AssetModal
            isOpen={isEditModalOpen}
            onClose={() => {
              setIsEditModalOpen(false);
              setCurrentAsset(null);
            }}
            title="Редактировать актив"
          >
            <EditAssetForm
              existingAsset={currentAsset}
              onSubmit={handleEditAsset}
              onClose={() => {
                setIsEditModalOpen(false);
                setCurrentAsset(null);
              }}
            />
          </AssetModal>

          <AssetModal
            isOpen={isDetailsModalOpen}
            onClose={() => setIsDetailsModalOpen(false)}
            title={`Детали: ${currentAsset.inventory_number}`}
          >
            <AssetDetailsModal
              asset={currentAsset}
              onClose={() => setIsDetailsModalOpen(false)}
              onEdit={handleEditClick}
              onDelete={handleDeleteAsset}
            />
          </AssetModal>
        </>
      )}
    </div>
  );
};

export default Assets;