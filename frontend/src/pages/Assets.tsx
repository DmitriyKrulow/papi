// frontend/src/pages/Assets.tsx
import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { AssetStatusMap } from '../types';
import { AssetTypeNames } from '../types';
import type { Asset, AssetTypeConfig } from '../types';
import { formatMoney } from '../utils/helpers';
import toast from 'react-hot-toast';
import { UserRole } from '../domain/roles';
import AssetModal from '../components/assets/AssetModal';
import AddAssetForm from '../components/assets/AddAssetForm';
import EditAssetForm from '../components/assets/EditAssetForm';
import AssetDetailsModal from '../components/assets/AssetDetailsModal';
import ImportAssetsModal from '../components/assets/ImportAssetsModal';
import {
  Package, Search, Eye, Plus, Upload, Edit, Trash2, Download,
  Filter, ChevronDown, ChevronUp, X,
  ArrowUpDown, ArrowUp, ArrowDown,
  MoreHorizontal, RefreshCw, ClipboardCheck, CheckCircle2, XCircle, Clock
} from 'lucide-react';

interface PaginatedResponse {
  items: Asset[];
  total: number;
  skip: number;
  limit: number;
}

type SortDirection = 'asc' | 'desc' | null;
type SortColumn = 'inventory_number' | 'name' | 'status' | 'current_value' | 'department_name' | 'responsible_person' | 'location_address';

interface SortConfig {
  column: SortColumn | null;
  direction: SortDirection;
}

const PAGE_SIZES = [10, 25, 50, 100];
const DEFAULT_PAGE_SIZE = 25;

const Assets: React.FC = () => {
  const navigate = useNavigate();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [totalAssets, setTotalAssets] = useState(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState<boolean>(false);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState<boolean>(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterAssetType, setFilterAssetType] = useState('');
  const [filterDepartment, setFilterDepartment] = useState('');
  const [filterLocation, setFilterLocation] = useState('');
  const [filterEmployee, setFilterEmployee] = useState('');
  const [currentAsset, setCurrentAsset] = useState<Asset | null>(null);
  const [assetTypeConfigs, setAssetTypeConfigs] = useState<AssetTypeConfig[]>([]);
  const [departments, setDepartments] = useState<Array<{id: number; name: string; code: string; location: string; full_name: string}>>([]);
  const [employees, setEmployees] = useState<Array<{id: number; full_name: string; position: string; department_name: string; department_code: string}>>([]);
  const [rooms, setRooms] = useState<Array<{id: number; name: string; floor?: string; building?: string; department_id: number; department_name: string; full_name: string}>>([]);
  const [filtersExpanded, setFiltersExpanded] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [sortConfig, setSortConfig] = useState<SortConfig>({ column: null, direction: null });
  const [roomSearch, setRoomSearch] = useState('');
  const [employeeSearch, setEmployeeSearch] = useState('');
  const [roomDropdownOpen, setRoomDropdownOpen] = useState(false);
  const [employeeDropdownOpen, setEmployeeDropdownOpen] = useState(false);
  const [departmentSearch, setDepartmentSearch] = useState('');
  const [deptDropdownOpen, setDeptDropdownOpen] = useState(false);

  const getAssetTypeLabel = (assetType: string | undefined): { icon: string; name: string } => {
    if (!assetType) return { icon: '📦', name: '—' };
    const config = AssetTypeNames[assetType];
    return config ? { icon: config.icon, name: config.label } : { icon: '📦', name: assetType };
  };

  const getSortedAndFilteredAssets = useMemo(() => {
    let result = [...assets];

    if (filterStatus) result = result.filter(a => a.status === filterStatus);
    if (filterAssetType) result = result.filter(a => a.asset_type === filterAssetType);
    if (filterDepartment) result = result.filter(a =>
      (a.department_name || '').toLowerCase().includes(filterDepartment.toLowerCase()) ||
      (a.department_code || '').toLowerCase().includes(filterDepartment.toLowerCase())
    );
    if (filterLocation) result = result.filter(a =>
      (a.location_address || '').toLowerCase().includes(filterLocation.toLowerCase())
    );
    if (filterEmployee) result = result.filter(a =>
      (a.employee_name || '').toLowerCase().includes(filterEmployee.toLowerCase()) ||
      (a.responsible_person || '').toLowerCase().includes(filterEmployee.toLowerCase())
    );

    if (sortConfig.column && sortConfig.direction) {
      result.sort((a, b) => {
        const aVal = a[sortConfig.column as keyof Asset];
        const bVal = b[sortConfig.column as keyof Asset];
        if (aVal == null && bVal == null) return 0;
        if (aVal == null) return 1;
        if (bVal == null) return -1;
        const comparison = String(aVal).localeCompare(String(bVal), 'ru');
        return sortConfig.direction === 'asc' ? comparison : -comparison;
      });
    }

    return result;
  }, [assets, filterStatus, filterAssetType, filterDepartment, filterLocation, filterEmployee, sortConfig]);

  const activeFilterCount = [filterStatus, filterAssetType, filterDepartment, filterLocation, filterEmployee].filter(Boolean).length;

  const totalFiltered = useMemo(() => {
    let count = totalAssets;
    if (filterStatus) count = assets.filter(a => a.status === filterStatus).length;
    if (filterAssetType) count = assets.filter(a => a.asset_type === filterAssetType).length;
    if (filterDepartment) count = assets.filter(a =>
      (a.department_name || '').toLowerCase().includes(filterDepartment.toLowerCase()) ||
      (a.department_code || '').toLowerCase().includes(filterDepartment.toLowerCase())
    ).length;
    return count;
  }, [totalAssets, assets, filterStatus, filterAssetType, filterDepartment]);

const getToken = async () => localStorage.getItem('token') || '';
  
  const getUserRole = () => {
    const token = localStorage.getItem('token');
    if (!token) return '';
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.role || '';
    } catch {
      return '';
    }
  };
const isAdmin = getUserRole() === UserRole.ADMIN;
  const [showHidden, setShowHidden] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchData = useCallback(async () => {
    const token = await getToken();
    const headers: Record<string, string> = {
      'Authorization': token ? `Bearer ${token}` : '',
    };

fetch('/api/asset-types/', { headers })
      .then(r => { if (r.ok) return r.json().then(setAssetTypeConfigs); })
      .catch(e => console.error('Failed to load asset types:', e));
    fetch('/api/admin/placement-assignments/departments', { headers })
      .then(r => { if (r.ok) return r.json().then(setDepartments); })
      .catch(e => console.error('Failed to load departments:', e));
    fetch('/api/admin/placement-assignments/employees', { headers })
      .then(r => { if (r.ok) return r.json().then(setEmployees); })
      .catch(e => console.error('Failed to load employees:', e));
    fetch('/api/admin/placement-assignments/rooms', { headers })
      .then(r => { if (r.ok) return r.json().then((data: any[]) => setRooms(
        data.map((room: any) => ({
          id: room.id,
          name: room.name,
          floor: room.floor,
          building: room.building,
          department_id: room.department_id,
          department_name: room.department_name || '',
          full_name: room.department_name ? `${room.department_name} - ${room.name}` : room.name,
        }))
      )); })
      .catch(e => console.error('Failed to load rooms:', e));
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleExport = async () => {
    try {
      const token = await getToken();
      const response = await fetch('/api/export/assets', {
        headers: { 'Authorization': token ? `Bearer ${token}` : '' },
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `assets_export_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success('Экспорт завершен');
      } else {
        toast.error('Ошибка экспорта');
      }
    } catch {
      toast.error('Ошибка соединения с сервером');
    }
  };

  const handleRestoreFromExcel = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    if (!window.confirm('ВНИМАНИЕ! Все текущие активы будут удалены и заменены данными из файла. Продолжить?')) {
      return;
    }
    
    try {
      const token = await getToken();
      const response = await fetch('/api/admin/assets/restore-from-excel', {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
        body: file,
      });
      
if (response.ok) {
        const result = await response.json();
        toast.success(`База восстановлена: удалено ${result.deleted}, создано ${result.created}`);
        fetchData(); // Перезагрузить вспомогательные данные
        setRefreshKey(k => k + 1); // Принудительно перезагрузить список активов
      }
    } catch (err: any) {
      toast.error('Ошибка соединения с сервером');
    } finally {
      e.target.value = ''; // Сбросить input
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
        const errorData = await response.json();
        toast.error(errorData.detail || 'Ошибка обновления актива');
      }
    } catch (err: any) {
      toast.error('Ошибка обновления актива');
    }
  };

const handleDeleteAsset = async (id: number) => {
    if (!window.confirm('Вы уверены, что хотите списать этот актив? Он будет скрыт из общего списка.')) return;
    try {
      const token = await getToken();
      const response = await fetch(`/api/assets/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });
      
      if (response.ok) {
        setAssets((prev) => prev.filter((a) => a.id !== id));
        setTotalAssets((prev) => Math.max(0, prev - 1));
        toast.success('Актив списан');
      } else {
        const errorData = await response.json();
        toast.error(errorData.detail || 'Ошибка удаления актива');
      }
    } catch (err: any) {
      toast.error('Ошибка удаления актива');
    }
  };

  const handleRestoreAsset = async (id: number) => {
    try {
      const token = await getToken();
      const response = await fetch(`/api/assets/${id}/restore`, {
        method: 'PUT',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });
      
      if (response.ok) {
        const updatedAsset = await response.json();
        setAssets((prev) => prev.map((a) => (a.id === id ? updatedAsset : a)));
        toast.success('Актив восстановлен');
        setIsDetailsModalOpen(false);
        setCurrentAsset(null);
      } else {
        const errorData = await response.json();
        toast.error(errorData.detail || 'Ошибка восстановления');
      }
    } catch (err: any) {
      toast.error('Ошибка соединения с сервером');
    }
  };

  const handleHardDeleteAsset = async (id: number) => {
    if (!window.confirm('ВНИМАНИЕ! Актив будет удален НАВСЕГДА вместе со всеми связанными заявками на ремонт. Это действие необратимо. Продолжить?')) return;
    try {
      const token = await getToken();
      const response = await fetch(`/api/assets/${id}/hard`, {
        method: 'DELETE',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });
      
      if (response.ok) {
        setAssets((prev) => prev.filter((a) => a.id !== id));
        setTotalAssets((prev) => Math.max(0, prev - 1));
        toast.success('Актив удален навсегда');
        setIsDetailsModalOpen(false);
        setCurrentAsset(null);
      } else {
        const errorData = await response.json();
        toast.error(errorData.detail || 'Ошибка удаления');
      }
    } catch (err: any) {
      toast.error('Ошибка соединения с сервером');
    }
  };

  const handleViewDetails = (asset: Asset) => {
    setCurrentAsset(asset);
    setIsDetailsModalOpen(true);
  };

const handleEditClick = (asset: Asset) => {
    setCurrentAsset(asset);
    setIsDetailsModalOpen(false);
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

  useEffect(() => {
    const loadAssets = async () => {
      try {
        setLoading(true);
        const skip = (currentPage - 1) * pageSize;
        const params = new URLSearchParams({
          skip: String(skip),
          limit: String(pageSize),
        });
        if (searchTerm) params.set('search', searchTerm);
if (filterStatus) params.set('status', filterStatus);
        if (filterDepartment) params.set('department', filterDepartment);
        if (showHidden) params.set('include_hidden', 'true');

        const token = await getToken();
        const response = await fetch(`/api/assets/?${params}`, {
          headers: { 'Authorization': token ? `Bearer ${token}` : '' },
        });

        if (response.ok) {
          const data: PaginatedResponse = await response.json();
          setAssets(data.items || []);
          setTotalAssets(data.total);
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
loadAssets();
  }, [currentPage, pageSize, searchTerm, filterStatus, filterDepartment, showHidden, refreshKey]);

  const handleSort = (column: SortColumn) => {
    setSortConfig(prev => ({
      column,
      direction: prev.column === column
        ? prev.direction === 'asc' ? 'desc' : prev.direction === 'desc' ? null : 'asc'
        : 'asc',
    }));
  };

  const SortIcon = ({ column }: { column: SortColumn }) => {
    if (sortConfig.column !== column) return <ArrowUpDown className="w-3 h-3 ml-1 opacity-40" />;
    if (sortConfig.direction === 'asc') return <ArrowUp className="w-3 h-3 ml-1" />;
    if (sortConfig.direction === 'desc') return <ArrowDown className="w-3 h-3 ml-1" />;
    return <ArrowUpDown className="w-3 h-3 ml-1 opacity-40" />;
  };

  if (loading && assets.length === 0) {
    return (
      <div className="flex justify-center items-center py-16">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
          <p className="mt-3 text-gray-500 text-sm">Загрузка активов...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
        <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>{error}</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Package className="w-7 h-7 text-blue-600" />
            Активы
          </h1>
          <p className="text-sm text-gray-500 mt-1">Всего: {totalAssets} в базе</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => navigate('/assets/create')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition flex items-center gap-2 whitespace-nowrap shadow-sm"
          >
            <Plus className="w-4 h-4" />
            Добавить
          </button>
          <button
            onClick={() => setIsImportModalOpen(true)}
            className="bg-white text-gray-700 border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 transition flex items-center gap-2 whitespace-nowrap"
          >
            <Upload className="w-4 h-4" />
            Импорт
          </button>
          <button
            onClick={handleExport}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition flex items-center gap-2 whitespace-nowrap shadow-sm"
          >
            <Download className="w-4 h-4" />
            Экспорт
          </button>
          {isAdmin && (
            <>
              <input
                type="file"
                id="restore-file"
                accept=".xlsx,.xls"
                onChange={handleRestoreFromExcel}
                className="hidden"
              />
              <button
                onClick={() => document.getElementById('restore-file')?.click()}
                className="bg-amber-600 text-white px-4 py-2 rounded-lg hover:bg-amber-700 transition flex items-center gap-2 whitespace-nowrap shadow-sm"
              >
                <RefreshCw className="w-4 h-4" />
                Восстановить из файла
              </button>
            </>
          )}
        </div>
      </div>

      {/* Search & Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Search className="w-4 h-4 text-gray-400 dark:text-gray-500" />
          <input
            type="text"
            placeholder="Поиск по названию, инв. номеру..."
            value={searchTerm}
            onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
          {isAdmin && (
            <button
              onClick={() => { setShowHidden(!showHidden); setCurrentPage(1); }}
              className={`px-3 py-2 rounded-lg transition flex items-center gap-1.5 whitespace-nowrap text-sm border ${
                showHidden
                  ? 'bg-amber-100 text-amber-700 border-amber-300 dark:bg-amber-900 dark:text-amber-300 dark:border-amber-700'
                  : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600'
              }`}
            >
              {showHidden ? '👁️' : '🙈'} Скрытые
            </button>
          )}
          <button
            onClick={() => setFiltersExpanded(!filtersExpanded)}
            className={`px-3 py-2 rounded-lg transition flex items-center gap-1.5 whitespace-nowrap text-sm border ${
              filtersExpanded || activeFilterCount > 0
                ? 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900 dark:text-blue-300 dark:border-blue-700'
                : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600'
            }`}
          >
            <Filter className="w-4 h-4" />
            <span className="hidden sm:inline">Фильтры</span>
            {activeFilterCount > 0 && (
              <span className="bg-blue-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {activeFilterCount}
              </span>
            )}
            {filtersExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
          {activeFilterCount > 0 && (
            <button
              onClick={() => { setFilterStatus(''); setFilterAssetType(''); setFilterDepartment(''); setFilterLocation(''); setFilterEmployee(''); setCurrentPage(1); }}
              className="px-3 py-2 text-sm text-blue-600 hover:text-blue-800 border border-blue-200 rounded-lg hover:bg-blue-50 transition whitespace-nowrap dark:text-blue-400 dark:hover:text-blue-300 dark:border-blue-700 dark:hover:bg-blue-900"
            >
              Сбросить
            </button>
          )}
        </div>

        {filtersExpanded && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-3 border-t border-gray-100 dark:border-gray-700">
            <select
              value={filterStatus}
              onChange={(e) => { setFilterStatus(e.target.value); setCurrentPage(1); }}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            >
              <option value="">Все статусы</option>
              {Object.entries(AssetStatusMap).map(([code, info]) => (
                <option key={code} value={code}>{info.label}</option>
              ))}
            </select>
            <select
              value={filterAssetType}
              onChange={(e) => { setFilterAssetType(e.target.value); setCurrentPage(1); }}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            >
              <option value="">Все типы</option>
              {assetTypeConfigs.map(config => (
                <option key={config.code} value={config.code}>{config.name}</option>
              ))}
            </select>
            <div className="relative">
              <div className="relative">
                <Search className="absolute left-2.5 top-2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
                <button
                  type="button"
                  onClick={() => { setDeptDropdownOpen(!deptDropdownOpen); setRoomDropdownOpen(false); setEmployeeDropdownOpen(false); }}
                  className="w-full pl-7 pr-8 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm text-left bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-600 transition"
                >
                  {filterDepartment
                    ? departments.find(d => d.code === filterDepartment)?.full_name
                    : 'Все подразделения'}
                </button>
                {filterDepartment && (
                  <button
                    onClick={(e) => { e.stopPropagation(); setFilterDepartment(''); setCurrentPage(1); }}
                    className="absolute right-7 top-1.5 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
                <ChevronDown className={`absolute right-2.5 top-2.5 w-3.5 h-3.5 text-gray-400 transition-transform ${deptDropdownOpen ? 'rotate-180' : ''}`} />
              </div>
              {deptDropdownOpen && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setDeptDropdownOpen(false)} />
                  <div className="absolute z-20 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-60 overflow-hidden" style={{ top: '100%' }}>
                    <div className="p-2 border-b border-gray-100 dark:border-gray-700">
                      <div className="relative">
                        <Search className="absolute left-2.5 top-2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
                        <input
                          type="text"
                          placeholder="Поиск..."
                          value={departmentSearch}
                          onChange={(e) => setDepartmentSearch(e.target.value)}
                          className="w-full pl-7 pr-2 py-1.5 border border-gray-200 dark:border-gray-600 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        />
                      </div>
                    </div>
                    <div className="overflow-y-auto max-h-48">
                      {departments
                        .filter(dept =>
                          !departmentSearch ||
                          dept.full_name.toLowerCase().includes(departmentSearch.toLowerCase()) ||
                          dept.code.toLowerCase().includes(departmentSearch.toLowerCase()) ||
                          dept.name.toLowerCase().includes(departmentSearch.toLowerCase())
                        )
                        .map(dept => (
                          <button
                            key={dept.id}
                            onClick={() => { setFilterDepartment(dept.code); setCurrentPage(1); setDeptDropdownOpen(false); setDepartmentSearch(''); }}
                            className={`w-full px-3 py-2 text-left text-sm hover:bg-blue-50 dark:hover:bg-gray-700 transition ${filterDepartment === dept.code ? 'bg-blue-50 text-blue-700 font-medium dark:bg-blue-900 dark:text-blue-300' : 'text-gray-700 dark:text-gray-300'}`}
                          >
                            <div className="truncate">{dept.full_name}</div>
                            <div className="text-xs text-gray-400 truncate dark:text-gray-500">{dept.code}</div>
                          </button>
                        ))}
                      {departments.filter(dept =>
                        !departmentSearch ||
                        dept.full_name.toLowerCase().includes(departmentSearch.toLowerCase()) ||
                        dept.code.toLowerCase().includes(departmentSearch.toLowerCase()) ||
                        dept.name.toLowerCase().includes(departmentSearch.toLowerCase())
                      ).length === 0 && (
                        <div className="px-3 py-4 text-sm text-gray-400 text-center dark:text-gray-500">Ничего не найдено</div>
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>
            <div className="relative">
              <div className="relative">
                <Search className="absolute left-2.5 top-2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
                <button
                  type="button"
                  onClick={() => { setRoomDropdownOpen(!roomDropdownOpen); setDeptDropdownOpen(false); setEmployeeDropdownOpen(false); }}
                  className="w-full pl-7 pr-8 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm text-left bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-600 transition"
                >
                  {filterLocation
                    ? rooms.find(r => r.name === filterLocation)?.full_name
                    : 'Все помещения'}
                </button>
                {filterLocation && (
                  <button
                    onClick={(e) => { e.stopPropagation(); setFilterLocation(''); setCurrentPage(1); }}
                    className="absolute right-7 top-1.5 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
                <ChevronDown className={`absolute right-2.5 top-2.5 w-3.5 h-3.5 text-gray-400 transition-transform ${roomDropdownOpen ? 'rotate-180' : ''}`} />
              </div>
              {roomDropdownOpen && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setRoomDropdownOpen(false)} />
                  <div className="absolute z-20 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-60 overflow-hidden" style={{ top: '100%' }}>
                    <div className="p-2 border-b border-gray-100 dark:border-gray-700">
                      <div className="relative">
                        <Search className="absolute left-2.5 top-2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
                        <input
                          type="text"
                          placeholder="Поиск..."
                          value={roomSearch}
                          onChange={(e) => setRoomSearch(e.target.value)}
                          className="w-full pl-7 pr-2 py-1.5 border border-gray-200 dark:border-gray-600 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        />
                      </div>
                    </div>
                    <div className="overflow-y-auto max-h-48">
                      {rooms
                        .filter(room =>
                          !roomSearch ||
                          room.full_name.toLowerCase().includes(roomSearch.toLowerCase()) ||
                          room.name.toLowerCase().includes(roomSearch.toLowerCase()) ||
                          (room.department_name || '').toLowerCase().includes(roomSearch.toLowerCase())
                        )
                        .map(room => (
                          <button
                            key={room.id}
                            onClick={() => { setFilterLocation(room.name); setCurrentPage(1); setRoomDropdownOpen(false); setRoomSearch(''); }}
                            className={`w-full px-3 py-2 text-left text-sm hover:bg-blue-50 dark:hover:bg-gray-700 transition ${filterLocation === room.name ? 'bg-blue-50 text-blue-700 font-medium dark:bg-blue-900 dark:text-blue-300' : 'text-gray-700 dark:text-gray-300'}`}
                          >
                            <div className="truncate">{room.full_name}</div>
                            {(room.floor || room.building) && (
                              <div className="text-xs text-gray-400 truncate dark:text-gray-500">
                                {room.floor ? `Этаж: ${room.floor}` : ''} {room.building ? `Корпус: ${room.building}` : ''}
                              </div>
                            )}
                          </button>
                        ))}
                      {rooms.filter(room =>
                        !roomSearch ||
                        room.full_name.toLowerCase().includes(roomSearch.toLowerCase()) ||
                        room.name.toLowerCase().includes(roomSearch.toLowerCase()) ||
                        (room.department_name || '').toLowerCase().includes(roomSearch.toLowerCase())
                      ).length === 0 && (
                        <div className="px-3 py-4 text-sm text-gray-400 text-center dark:text-gray-500">Ничего не найдено</div>
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>
            <div className="relative">
              <div className="relative">
                <Search className="absolute left-2.5 top-2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
                <button
                  type="button"
                  onClick={() => { setEmployeeDropdownOpen(!employeeDropdownOpen); setDeptDropdownOpen(false); setRoomDropdownOpen(false); }}
                  className="w-full pl-7 pr-8 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm text-left bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-600 transition"
                >
                  {filterEmployee
                    ? employees.find(e => e.full_name === filterEmployee)?.full_name
                    : 'Все сотрудники'}
                </button>
                {filterEmployee && (
                  <button
                    onClick={(e) => { e.stopPropagation(); setFilterEmployee(''); setCurrentPage(1); }}
                    className="absolute right-7 top-1.5 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
                <ChevronDown className={`absolute right-2.5 top-2.5 w-3.5 h-3.5 text-gray-400 transition-transform ${employeeDropdownOpen ? 'rotate-180' : ''}`} />
              </div>
              {employeeDropdownOpen && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setEmployeeDropdownOpen(false)} />
                  <div className="absolute z-20 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-60 overflow-hidden" style={{ top: '100%' }}>
                    <div className="p-2 border-b border-gray-100 dark:border-gray-700">
                      <div className="relative">
                        <Search className="absolute left-2.5 top-2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
                        <input
                          type="text"
                          placeholder="Поиск..."
                          value={employeeSearch}
                          onChange={(e) => setEmployeeSearch(e.target.value)}
                          className="w-full pl-7 pr-2 py-1.5 border border-gray-200 dark:border-gray-600 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        />
                      </div>
                    </div>
                    <div className="overflow-y-auto max-h-48">
                      {employees
                        .filter(emp =>
                          !employeeSearch ||
                          emp.full_name.toLowerCase().includes(employeeSearch.toLowerCase()) ||
                          (emp.position || '').toLowerCase().includes(employeeSearch.toLowerCase()) ||
                          (emp.department_name || '').toLowerCase().includes(employeeSearch.toLowerCase())
                        )
                        .map(emp => (
                          <button
                            key={emp.id}
                            onClick={() => { setFilterEmployee(emp.full_name); setCurrentPage(1); setEmployeeDropdownOpen(false); setEmployeeSearch(''); }}
                            className={`w-full px-3 py-2 text-left text-sm hover:bg-blue-50 dark:hover:bg-gray-700 transition ${filterEmployee === emp.full_name ? 'bg-blue-50 text-blue-700 font-medium dark:bg-blue-900 dark:text-blue-300' : 'text-gray-700 dark:text-gray-300'}`}
                          >
                            <div className="truncate">{emp.full_name}</div>
                            {emp.position && (
                              <div className="text-xs text-gray-400 truncate dark:text-gray-500">{emp.position}</div>
                            )}
                          </button>
                        ))}
                      {employees.filter(emp =>
                        !employeeSearch ||
                        emp.full_name.toLowerCase().includes(employeeSearch.toLowerCase()) ||
                        (emp.position || '').toLowerCase().includes(employeeSearch.toLowerCase()) ||
                        (emp.department_name || '').toLowerCase().includes(employeeSearch.toLowerCase())
                      ).length === 0 && (
                        <div className="px-3 py-4 text-sm text-gray-400 text-center dark:text-gray-500">Ничего не найдено</div>
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Table / Mobile Cards */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {getSortedAndFilteredAssets.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">📭</div>
            <p className="text-gray-500 dark:text-gray-400">
              {searchTerm || filterStatus || filterAssetType || filterDepartment || filterLocation || filterEmployee
                ? 'Ничего не найдено по заданным параметрам'
                : 'Нет активов для отображения'}
            </p>
            {(searchTerm || filterStatus || filterAssetType || filterDepartment || filterLocation || filterEmployee) && (
              <button
                onClick={() => { setSearchTerm(''); setFilterStatus(''); setFilterAssetType(''); setFilterDepartment(''); setFilterLocation(''); setFilterEmployee(''); setCurrentPage(1); }}
                className="mt-3 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
              >
                Сбросить фильтры
              </button>
            )}
          </div>
        ) : (
          <>
            {/* Desktop Table (>=768px) */}
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-700 border-b">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider border-r border-gray-100 dark:border-gray-600">
                      <button onClick={() => handleSort('inventory_number')} className="flex items-center hover:text-gray-700 dark:hover:text-gray-300 transition">
                        Инв. номер <SortIcon column="inventory_number" />
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider border-r border-gray-100 dark:border-gray-600">
                      <button onClick={() => handleSort('name')} className="flex items-center hover:text-gray-700 dark:hover:text-gray-300 transition">
                        Название <SortIcon column="name" />
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider border-r border-gray-100 dark:border-gray-600">
                      Тип
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider border-r border-gray-100 dark:border-gray-600">
                      <button onClick={() => handleSort('current_value')} className="flex items-center hover:text-gray-700 dark:hover:text-gray-300 transition">
                        Стоимость <SortIcon column="current_value" />
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider border-r border-gray-100 dark:border-gray-600">
                      Статус
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider border-r border-gray-100 dark:border-gray-600">
                      <button onClick={() => handleSort('department_name')} className="flex items-center hover:text-gray-700 dark:hover:text-gray-300 transition">
                        Подразделение <SortIcon column="department_name" />
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider border-r border-gray-100 dark:border-gray-600">
                      Сотрудник
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider border-r border-gray-100 dark:border-gray-600">
                      <button onClick={() => handleSort('location_address')} className="flex items-center hover:text-gray-700 dark:hover:text-gray-300 transition">
                        Местоположение <SortIcon column="location_address" />
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider border-r border-gray-100 dark:border-gray-600">
                      <button onClick={() => handleSort('responsible_person')} className="flex items-center hover:text-gray-700 dark:hover:text-gray-300 transition">
                        Ответственный <SortIcon column="responsible_person" />
                      </button>
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider border-r border-gray-100 dark:border-gray-600 w-28">
                      Проверка
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider w-24">
                      Действия
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {getSortedAndFilteredAssets.map((asset) => {
                    const typeInfo = getAssetTypeLabel(asset.asset_type);
                    return (
                      <tr key={asset.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition">
                        <td className="px-4 py-3 text-sm font-mono text-gray-900 dark:text-gray-100 border-r border-gray-50 dark:border-gray-700">
                          {asset.inventory_number}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100 font-medium border-r border-gray-50 dark:border-gray-700">
                          {asset.name}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 border-r border-gray-50 dark:border-gray-700">
                          {typeInfo.icon} {typeInfo.name}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100 border-r border-gray-50 dark:border-gray-700">
                          {formatMoney(asset.current_value)}
                        </td>
                        <td className="px-4 py-3 border-r border-gray-50 dark:border-gray-700">
                          {getStatusBadge(asset.status)}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 border-r border-gray-50 dark:border-gray-700">
                          {asset.department_name || asset.department_code || '—'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 border-r border-gray-50 dark:border-gray-700">
                          {asset.employee_name || '—'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 border-r border-gray-50 dark:border-gray-700">
                          {asset.location_address || '—'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                          {asset.responsible_person || '—'}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {asset.last_inventory_confirmed ? (
                            <div className="flex flex-col items-center gap-0.5">
                              <CheckCircle2 className="w-4 h-4 text-green-500" />
                              <span className="text-[10px] text-gray-400 truncate max-w-[80px]" title={asset.last_inventory_date}>
                                {asset.last_inventory_date ? new Date(asset.last_inventory_date).toLocaleDateString('ru-RU') : '—'}
                              </span>
                            </div>
                          ) : asset.last_inventory_date ? (
                            <div className="flex flex-col items-center gap-0.5">
                              <Clock className="w-4 h-4 text-amber-500" />
                              <span className="text-[10px] text-gray-400 truncate max-w-[80px]" title={asset.last_inventory_date}>
                                {new Date(asset.last_inventory_date).toLocaleDateString('ru-RU')}
                              </span>
                            </div>
                          ) : (
                            <div className="flex flex-col items-center gap-0.5">
                              <ClipboardCheck className="w-4 h-4 text-gray-300 dark:text-gray-600" />
                              <span className="text-[10px] text-gray-400">—</span>
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <div className="flex items-center justify-center gap-1">
                            <button
                              onClick={() => { setCurrentAsset(asset); setIsDetailsModalOpen(true); }}
                              className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition dark:hover:bg-gray-700"
                              title="Просмотреть"
                              aria-label="Просмотреть"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => { setCurrentAsset(asset); setIsEditModalOpen(true); }}
                              className="p-1.5 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition dark:hover:bg-gray-700"
                              title="Редактировать"
                              aria-label="Редактировать"
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteAsset(asset.id)}
                              className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition dark:hover:bg-gray-700"
                              title="Скрыть актив"
                              aria-label="Скрыть актив"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Mobile Cards (<768px) */}
            <div className="md:hidden divide-y divide-gray-200 dark:divide-gray-700">
              {getSortedAndFilteredAssets.map((asset) => {
                const typeInfo = getAssetTypeLabel(asset.asset_type);
                return (
                  <div 
                    key={asset.id} 
                    className="p-4 space-y-2 active:bg-gray-50 dark:active:bg-gray-700 transition cursor-pointer"
                    onClick={() => { setCurrentAsset(asset); setIsDetailsModalOpen(true); }}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-mono font-semibold text-gray-900 dark:text-gray-100 truncate">
                          {asset.inventory_number}
                        </div>
                        <div className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                          {asset.name}
                        </div>
                      </div>
                      {getStatusBadge(asset.status)}
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="text-gray-600 dark:text-gray-400">
                        {typeInfo.icon} {typeInfo.name}
                      </div>
                      <div className="text-gray-900 dark:text-gray-100 font-medium">
                        {formatMoney(asset.current_value)}
                      </div>
                      <div className="text-gray-600 dark:text-gray-400 col-span-2 truncate">
                        🏢 {asset.department_name || asset.department_code || '—'}
                      </div>
                      <div className="text-gray-600 dark:text-gray-400 truncate">
                        👤 {asset.employee_name || '—'}
                      </div>
                      <div className="text-gray-600 dark:text-gray-400 truncate">
                        📍 {asset.location_address || '—'}
                      </div>
                      <div className="text-gray-600 dark:text-gray-400 col-span-2 truncate">
                        🎯 {asset.responsible_person || '—'}
                      </div>
                      {/* Строка проверки наличия */}
                      <div className="col-span-2 flex items-center gap-2 text-xs pt-1">
                        {asset.last_inventory_confirmed ? (
                          <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                        ) : asset.last_inventory_date ? (
                          <Clock className="w-4 h-4 text-amber-500 flex-shrink-0" />
                        ) : (
                          <ClipboardCheck className="w-4 h-4 text-gray-300 dark:text-gray-600 flex-shrink-0" />
                        )}
                        <span className="text-gray-500 dark:text-gray-400 truncate">
                          {asset.last_inventory_confirmed ? 'Подтверждён' : asset.last_inventory_date ? `Проверен ${new Date(asset.last_inventory_date).toLocaleDateString('ru-RU')}` : 'Не проверен'}
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-2 pt-2 border-t border-gray-200 dark:border-gray-700" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => { setCurrentAsset(asset); setIsDetailsModalOpen(true); }}
                        className="flex-1 px-3 py-2 text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/50 transition font-medium"
                      >
                        👁️ Просмотр
                      </button>
                      <button
                        onClick={() => { setCurrentAsset(asset); setIsEditModalOpen(true); }}
                        className="flex-1 px-3 py-2 text-xs bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-400 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/50 transition font-medium"
                      >
                        ✏️ Изменить
                      </button>
                      <button
                        onClick={() => handleDeleteAsset(asset.id)}
                        className="px-3 py-2 text-xs bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/50 transition"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Pagination */}
            <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <span>Показано:</span>
                <select
                  value={pageSize}
                  onChange={(e) => { setPageSize(Number(e.target.value)); setCurrentPage(1); }}
                  className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                  {PAGE_SIZES.map(size => (
                    <option key={size} value={size}>{size}</option>
                  ))}
                </select>
                <span>из {totalFiltered} записей</span>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setCurrentPage(1)}
                  disabled={currentPage === 1}
                  className="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed text-gray-700 dark:text-gray-300"
                >
                  ‹‹
                </button>
                <button
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed text-gray-700 dark:text-gray-300"
                >
                  ‹
                </button>
                <span className="px-3 py-1 text-sm text-gray-700 dark:text-gray-300">
                  Стр. {currentPage}
                </span>
                <button
                  onClick={() => setCurrentPage(p => p + 1)}
                  disabled={currentPage * pageSize >= totalFiltered}
                  className="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed text-gray-700 dark:text-gray-300"
                >
                  ›
                </button>
                <button
                  onClick={() => setCurrentPage(p => p + 1)}
                  disabled={currentPage * pageSize >= totalFiltered}
                  className="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed text-gray-700 dark:text-gray-300"
                >
                  ››
                </button>
              </div>
            </div>
          </>
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
        onSuccess={() => { setCurrentPage(1); setRefreshKey(k => k + 1); }}
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
            className="max-w-4xl"
          >
<AssetDetailsModal
              asset={currentAsset}
              onClose={() => setIsDetailsModalOpen(false)}
              onEdit={handleEditClick}
              onDelete={handleDeleteAsset}
              onHardDelete={isAdmin ? handleHardDeleteAsset : undefined}
              onRestore={isAdmin ? handleRestoreAsset : undefined}
            />
          </AssetModal>
        </>
      )}
    </div>
  );
};

export default Assets;