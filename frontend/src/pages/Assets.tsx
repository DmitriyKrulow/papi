// frontend/src/pages/Assets.tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Asset, AssetTypeConfig } from '../types';
import { AssetStatusMap } from '../types';
import { formatMoney } from '../utils/helpers';
import toast from 'react-hot-toast';
import AssetModal from '../components/assets/AssetModal';
import AddAssetForm from '../components/assets/AddAssetForm';
import EditAssetForm from '../components/assets/EditAssetForm';
import AssetDetailsModal from '../components/assets/AssetDetailsModal';
import ImportAssetsModal from '../components/assets/ImportAssetsModal';
import { useAuth } from '../hooks/useAuth';

const Assets: React.FC = () => {
  const navigate = useNavigate();
  const { getToken } = useAuth();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState<boolean>(false);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState<boolean>(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterAssetType, setFilterAssetType] = useState('');
  const [filterLocation, setFilterLocation] = useState('');
  const [filterDepartment, setFilterDepartment] = useState('');
  const [filterResponsible, setFilterResponsible] = useState('');
  const [filterEmployee, setFilterEmployee] = useState('');
  const [currentAsset, setCurrentAsset] = useState<Asset | null>(null);
  const [assetTypeConfigs, setAssetTypeConfigs] = useState<AssetTypeConfig[]>([]);
  const [departments, setDepartments] = useState<Array<{id: number; name: string; code: string; location: string; full_name: string}>>([]);
  const [employees, setEmployees] = useState<Array<{id: number; full_name: string; position: string; department_name: string; department_code: string}>>([]);
  const [deptSearch, setDeptSearch] = useState('');
  const [empSearch, setEmpSearch] = useState('');

  const getAssetTypeIcon = (assetType: string | undefined): string => {
    if (!assetType) return '📦';
    const config = assetTypeConfigs.find(c => c.code === assetType);
    return config?.icon || '📦';
  };

  const filteredAssets = assets.filter((asset) => {
    const matchesSearch =
      asset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.inventory_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (asset.responsible_person || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = !filterStatus || asset.status === filterStatus;
    const matchesAssetType = !filterAssetType || asset.asset_type === filterAssetType;
    const matchesLocation = !filterLocation || (asset.location_address || '').toLowerCase().includes(filterLocation.toLowerCase());
    const matchesDepartment = !filterDepartment || 
      (asset.department_code || '').toLowerCase().includes(filterDepartment.toLowerCase()) ||
      (asset.department_name || '').toLowerCase().includes(filterDepartment.toLowerCase());
    const matchesResponsible = !filterResponsible || (asset.responsible_person || '').toLowerCase().includes(filterResponsible.toLowerCase());
    const matchesEmployee = !filterEmployee || 
      (asset.employee_name || '').toLowerCase().includes(filterEmployee.toLowerCase()) ||
      (asset.responsible_person || '').toLowerCase().includes(filterEmployee.toLowerCase());
    return matchesSearch && matchesStatus && matchesAssetType && matchesLocation && matchesDepartment && matchesResponsible && matchesEmployee;
  });

  const fetchAssets = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      const response = await fetch('/api/assets/?limit=10000', {
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

  useEffect(() => {
    fetchAssets();
    fetchAssetTypes();
    fetchDepartments();
    fetchEmployees();
  }, []);

  const fetchAssetTypes = async () => {
    try {
      const token = await getToken();
      const response = await fetch('/api/asset-types/', {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });
      if (response.ok) {
        const data = await response.json();
        setAssetTypeConfigs(data);
      }
    } catch (err) {
      console.error('Ошибка загрузки типов:', err);
    }
  };

  const fetchDepartments = async () => {
    try {
      const token = await getToken();
      const params = deptSearch ? `?search=${encodeURIComponent(deptSearch)}` : '';
      const response = await fetch(`/api/admin/placement-assignments/departments${params}`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });
      if (response.ok) {
        const data = await response.json();
        setDepartments(data);
      }
    } catch (err) {
      console.error('Ошибка загрузки подразделений:', err);
    }
  };

  const fetchEmployees = async () => {
    try {
      const token = await getToken();
      const params = empSearch ? `?search=${encodeURIComponent(empSearch)}` : '';
      const response = await fetch(`/api/admin/placement-assignments/employees${params}`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });
      if (response.ok) {
        const data = await response.json();
        setEmployees(data);
      }
    } catch (err) {
      console.error('Ошибка загрузки сотрудников:', err);
    }
  };

  const handleAddAsset = async (asset: Omit<Asset, 'id' | 'created_at' | 'updated_at'>) => {
    try {
      const token = await getToken();
      const response = await fetch('/api/assets/', {
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
        const errorData = await response.json();
        toast.error(errorData.detail || 'Ошибка добавления актива');
      }
    } catch (err: any) {
      toast.error('Ошибка добавления актива');
    }
  };

  const handleEditAsset = async (asset: Asset) => {
    try {
      const token = await getToken();
      const response = await fetch(`/api/assets/${asset.id}/`, {
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
        const errorData = await response.json();
        toast.error(errorData.detail || 'Ошибка обновления актива');
      }
    } catch (err: any) {
      toast.error('Ошибка обновления актива');
    }
  };

  const handleDeleteAsset = async (id: number) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот актив?')) return;
    try {
      const token = await getToken();
      const response = await fetch(`/api/assets/${id}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });
      
      if (response.ok) {
        setAssets((prev) => prev.filter((a) => a.id !== id));
        toast.success('Актив удален');
      } else {
        const errorData = await response.json();
        toast.error(errorData.detail || 'Ошибка удаления актива');
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
        <div className="flex gap-2 flex-wrap flex-1 max-w-2xl">
          <input
            type="text"
            placeholder="Поиск по названию или инв. номеру..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent flex-1 min-w-[200px]"
          />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Все статусы</option>
            <option value="active">Активен</option>
            <option value="maintenance">На ремонте</option>
            <option value="reserved">В резерве</option>
            <option value="decommissioned">Выведен</option>
            <option value="lost">Утерян</option>
            <option value="written_off">Списан</option>
          </select>
          <select
            value={filterAssetType}
            onChange={(e) => setFilterAssetType(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Все типы</option>
            {assetTypeConfigs.map(config => (
              <option key={config.code} value={config.code}>{config.icon} {config.name}</option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Поиск по размещению..."
            value={filterLocation}
            onChange={(e) => setFilterLocation(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent min-w-[180px]"
          />
          <select
            value={filterDepartment}
            onChange={(e) => setFilterDepartment(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent min-w-[200px]"
          >
            <option value="">Все подразделения</option>
            {departments.map(dept => (
              <option key={dept.id} value={dept.code}>{dept.full_name}</option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Поиск по человеку..."
            value={filterResponsible}
            onChange={(e) => setFilterResponsible(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent min-w-[180px]"
          />
          <select
            value={filterEmployee}
            onChange={(e) => setFilterEmployee(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent min-w-[200px]"
          >
            <option value="">Все сотрудники</option>
            {employees.map(emp => (
              <option key={emp.id} value={emp.full_name}>{emp.full_name} — {emp.position || 'без должности'}</option>
            ))}
          </select>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => navigate('/assets/create')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition flex items-center gap-2 whitespace-nowrap"
          >
            <span>➕</span> Добавить актив
          </button>
          <button
            onClick={() => setIsImportModalOpen(true)}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition flex items-center gap-2 whitespace-nowrap"
          >
            <span>📤</span> Загрузить из файла
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        {filteredAssets.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">📭</div>
            <p className="text-gray-500">
              {searchTerm ? 'Ничего не найдено' : 'Нет активов для отображения'}
            </p>
            {searchTerm && (
              <p className="text-gray-400 text-sm mt-1">
                Попробуйте изменить параметры поиска
              </p>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Инв. номер
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Название
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Тип
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Стоимость
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Статус
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Подразделение
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Ответственный
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Сотрудники
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Местоположение
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Действия
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredAssets.map((asset) => (
                  <tr key={asset.id} className="hover:bg-gray-50 transition">
                    <td className="px-6 py-4 text-sm font-mono text-gray-900">
                      {asset.inventory_number}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {asset.name}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {getAssetTypeIcon(asset.asset_type)} {asset.asset_type || '—'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {formatMoney(asset.current_value)}
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(asset.status)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {asset.department_name || asset.department_code || '—'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {asset.responsible_person || '—'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {asset.employee_name || '—'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {asset.location_address || '—'}
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

        {filteredAssets.length > 0 && (
          <div className="px-6 py-4 border-t text-sm text-gray-500">
            Найдено активов: {filteredAssets.length}
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

      <ImportAssetsModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onSuccess={fetchAssets}
      />

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