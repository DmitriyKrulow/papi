import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useRepairs } from '../hooks/useRepairs';
import { useAuth } from '../hooks/useAuth';
import RepairForm from '../components/forms/RepairForm';
import type { Asset } from '../types';

const RepairCreate: React.FC = () => {
  const { createRepair, loading } = useRepairs();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [selectedAssetId, setSelectedAssetId] = useState<number | ''>('');
  const [formTemplateData, setFormTemplateData] = useState<{ title: string; description: string } | null>(null);
  const [allAssets, setAllAssets] = useState<Asset[]>([]);
  const [assetsLoading, setAssetsLoading] = useState(true);
  const [assetSearch, setAssetSearch] = useState('');
  const [assetStatusFilter, setAssetStatusFilter] = useState('');
  const [assetDropdownOpen, setAssetDropdownOpen] = useState(false);
  const assetDropdownRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchAllAssets = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/assets/?limit=10000', {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (response.ok) {
          const data = await response.json();
          setAllAssets(data.items || data);
        }
      } catch (err) {
        console.error('Failed to fetch assets:', err);
      } finally {
        setAssetsLoading(false);
      }
    };
    fetchAllAssets();
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (assetDropdownRef.current && !assetDropdownRef.current.contains(event.target as Node)) {
        setAssetDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filteredAssets = allAssets.filter((asset) => {
    const matchesSearch = !assetSearch ||
      asset.name.toLowerCase().includes(assetSearch.toLowerCase()) ||
      asset.inventory_number.toLowerCase().includes(assetSearch.toLowerCase()) ||
      (asset.model || '').toLowerCase().includes(assetSearch.toLowerCase()) ||
      (asset.responsible_person || '').toLowerCase().includes(assetSearch.toLowerCase());
    const matchesStatus = !assetStatusFilter || asset.status === assetStatusFilter;
    return matchesSearch && matchesStatus;
  });

  const selectedAsset = allAssets.find((a) => a.id === selectedAssetId);

  const handleSubmit = async (data: any) => {
    try {
      const assetId = selectedAssetId ? Number(selectedAssetId) : (data.asset_id || 0);
      if (!assetId) {
        toast.error('Пожалуйста, выберите актив');
        return;
      }
      const formData: any = {
        asset_id: assetId,
        title: data.title || formTemplateData?.title || '',
        description: data.description || formTemplateData?.description || '',
        priority: data.priority || 'medium',
        created_by: user?.id || 0,
      };
      if (data.desired_completion_date) {
        formData.desired_completion_date = new Date(data.desired_completion_date).toISOString();
      }
      if (data.deadline) {
        formData.deadline = new Date(data.deadline).toISOString();
      }
      if (data.estimated_cost && Number(data.estimated_cost) > 0) {
        formData.estimated_cost = Number(data.estimated_cost);
      }
      await createRepair(formData);
      toast.success('Заявка на ремонт создана');
      navigate('/repairs');
    } catch (error) {
      toast.error('Ошибка при создании заявки');
    }
  };

  const applyTemplateToForm = useCallback((template: { title: string; description: string }) => {
    const asset = allAssets.find((a) => a.id === Number(selectedAssetId));
    const assetInfo = asset ? `Актив: ${asset.name} (ID: ${asset.id})` : '';
    const title = `${template.title}${assetInfo ? ' - ' + assetInfo : ''}`;
    const description = `${template.description}\n\n${assetInfo}\n\nДополнительная информация о проблеме:`;
    setFormTemplateData({ title, description });
  }, [allAssets, selectedAssetId]);

  const templateOptions = [
    {
      id: 'template_electrical',
      title: 'Электрические проблемы',
      description: 'Проблемы с электрическими цепями, проводкой, розетками',
    },
    {
      id: 'template_mechanical',
      title: 'Механические повреждения',
      description: 'Износ механизмов, шум, вибрация, скрипы',
    },
    {
      id: 'template_software',
      title: 'Проблемы ПО',
      description: 'Сбои в программном обеспечении, обновления',
    },
    {
      id: 'template_network',
      title: 'Сетевые проблемы',
      description: 'Проблемы с сетевым подключением, маршрутизацией',
    },
  ];

  const statusLabels: Record<string, string> = {
    active: 'Активен',
    maintenance: 'На ремонте',
    reserved: 'В резерве',
    decommissioned: 'Выведен',
    lost: 'Утерян',
    written_off: 'Списан',
  };

  if (assetsLoading) {
    return <div className="max-w-7xl mx-auto py-8 px-4"><div className="flex justify-center py-8"><div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div><span className="ml-3 text-gray-600 dark:text-gray-400">Загрузка активов...</span></div></div>;
  }

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Новая заявка на ремонт</h1>
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
          Создайте заявку на ремонт оборудования или систем
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 border border-gray-100 dark:border-gray-700">
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">Шаблоны заявок</label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {templateOptions.map((template) => (
              <button
                key={template.id}
                onClick={() => applyTemplateToForm(template)}
                className="text-left p-4 border border-gray-200 dark:border-gray-600 rounded-lg hover:border-blue-500 dark:hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
              >
                <h3 className="font-medium text-blue-600 dark:text-blue-400">{template.title}</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{template.description}</p>
              </button>
            ))}
          </div>
        </div>

        <RepairForm
          onSubmit={handleSubmit}
          loading={loading}
          assetId={Number(selectedAssetId) || undefined}
          assets={allAssets}
          defaultValue={formTemplateData || undefined}
        />

        <div className="mt-6" ref={assetDropdownRef}>
          <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">Выберите актив</label>
          <div className="relative">
            <div
              onClick={() => setAssetDropdownOpen(!assetDropdownOpen)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 dark:text-gray-100 cursor-pointer min-h-[42px] flex items-center justify-between"
            >
              <span className={selectedAsset ? '' : 'text-gray-400 dark:text-gray-500'}>
                {selectedAsset
                  ? `${selectedAsset.name} (ID: ${selectedAsset.id} - ${selectedAsset.inventory_number})`
                  : '-- Выберите актив --'}
              </span>
              <span className="text-gray-400 dark:text-gray-500 text-sm">{assetDropdownOpen ? '▲' : '▼'}</span>
            </div>

            {assetDropdownOpen && (
              <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-lg max-h-80 overflow-hidden">
                <div className="p-3 border-b border-gray-200 dark:border-gray-700 space-y-2">
                  <input
                    type="text"
                    placeholder="Поиск по названию, инвентарному номеру, модели..."
                    value={assetSearch}
                    onChange={(e) => setAssetSearch(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                    onClick={(e) => e.stopPropagation()}
                  />
                  <select
                    value={assetStatusFilter}
                    onChange={(e) => setAssetStatusFilter(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <option value="">Все статусы</option>
                    <option value="active">Активен</option>
                    <option value="reserved">В резерве</option>
                    <option value="maintenance">На ремонте</option>
                    <option value="decommissioned">Выведен</option>
                    <option value="lost">Утерян</option>
                    <option value="written_off">Списан</option>
                  </select>
                </div>

                <div className="overflow-y-auto max-h-56">
                  {filteredAssets.length === 0 ? (
                    <div className="px-3 py-4 text-sm text-gray-500 dark:text-gray-400 text-center">
                      {allAssets.length === 0 ? 'Активы не найдены' : 'Ничего не найдено'}
                    </div>
                  ) : (
                    filteredAssets.map((asset) => (
                      <button
                        key={asset.id}
                        onClick={() => {
                          setSelectedAssetId(asset.id);
                          setAssetDropdownOpen(false);
                          setAssetSearch('');
                          setAssetStatusFilter('');
                        }}
                        className={`w-full text-left px-3 py-2 hover:bg-blue-50 dark:hover:bg-blue-900/20 text-sm border-b border-gray-100 dark:border-gray-700 ${selectedAssetId === asset.id ? 'bg-blue-50 dark:bg-blue-900/30' : 'bg-white dark:bg-gray-800'}`}
                      >
                        <div className="font-medium text-gray-900 dark:text-gray-100">{asset.name}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          ID: {asset.id} | {asset.inventory_number}
                          {asset.model && ` | ${asset.model}`}
                        </div>
                        <div className="text-xs">
                          <span className={`px-1.5 py-0.5 rounded-full ${
                            asset.status === 'active' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' :
                            asset.status === 'maintenance' ? 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300' :
                            asset.status === 'reserved' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300' :
                            asset.status === 'decommissioned' ? 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300' :
                            asset.status === 'lost' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300' :
                            'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                          }`}>
                            {statusLabels[asset.status] || asset.status}
                          </span>
                          {asset.responsible_person && (
                            <span className="ml-2 text-gray-400 dark:text-gray-500">| {asset.responsible_person}</span>
                          )}
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Выбор актива поможет автоматически заполнить информацию о ремонтируемом оборудовании
          </p>
        </div>
      </div>
    </div>
  );
};

export default RepairCreate;
