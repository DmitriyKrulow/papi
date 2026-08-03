// frontend/src/pages/Marking.tsx
import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../hooks/useAuth';
import {
  Printer, Settings, CheckSquare, Square, Download,
  Tag, Search, Eye, Printer as PrinterIcon, CheckCircle2, XCircle
} from 'lucide-react';
import toast from 'react-hot-toast';

interface MarkingAsset {
  id: number;
  inventory_number: string;
  name: string;
  responsible: string;
  responsible_initials: string;
  purchase_date: string | null;
  commissioning_date: string | null;
  location: string;
  department: string;
  status?: string;
}

interface MarkingSettings {
  company_name: string;
  company_short: string;
  label_width: number;
  label_height: number;
  labels_per_row: number;
  labels_per_page: number;
}

const Marking: React.FC = () => {
  const { user } = useAuth();
  const [assets, setAssets] = useState<MarkingAsset[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [settings, setSettings] = useState<MarkingSettings>({
    company_name: 'ООО «ПАО»',
    company_short: 'ПАО',
    label_width: 105,
    label_height: 37,
    labels_per_row: 3,
    labels_per_page: 21,
  });
  const [showSettings, setShowSettings] = useState(false);
  const [previewAsset, setPreviewAsset] = useState<MarkingAsset | null>(null);
  const [previewHtml, setPreviewHtml] = useState('');
  const [batchHtml, setBatchHtml] = useState('');
  const [showBatchPreview, setShowBatchPreview] = useState(false);
  const printRef = useRef<HTMLDivElement>(null);

  const isAdmin = user?.role === 'admin';
  const isResponsible = user?.role === 'ответственный' || user?.role === 'responsible';
  const canAccess = isAdmin || isResponsible;

  useEffect(() => {
    if (!canAccess) {
      toast.error('Доступ запрещён');
      return;
    }
    fetchAssets();
    fetchSettings();
  }, [canAccess]);

  const fetchAssets = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (search) params.append('search', search);
      
      const res = await fetch(`/api/marking/assets?${params.toString()}`, {
        headers: localStorage.getItem('token') ? { 'Authorization': `Bearer ${localStorage.getItem('token')}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setAssets(data);
      }
    } catch {
      toast.error('Ошибка загрузки активов');
    } finally {
      setLoading(false);
    }
  };

  const fetchSettings = async () => {
    try {
      const res = await fetch('/api/marking/settings', {
        headers: localStorage.getItem('token') ? { 'Authorization': `Bearer ${localStorage.getItem('token')}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setSettings(data);
      }
    } catch {
      // Ignore
    }
  };

  const toggleSelect = (id: number) => {
    const newSet = new Set(selectedIds);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    setSelectedIds(newSet);
  };

  const selectAll = () => {
    if (selectedIds.size === filteredAssets.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredAssets.map(a => a.id)));
    }
  };

  const filteredAssets = assets.filter(asset => {
    if (statusFilter && asset.status !== statusFilter) return false;
    if (search) {
      const s = search.toLowerCase();
      return (
        asset.name.toLowerCase().includes(s) ||
        asset.inventory_number.toLowerCase().includes(s) ||
        asset.responsible.toLowerCase().includes(s)
      );
    }
    return true;
  });

  const previewSingle = async (asset: MarkingAsset) => {
    try {
      const res = await fetch(`/api/marking/label-html/${asset.id}`, {
        headers: localStorage.getItem('token') ? { 'Authorization': `Bearer ${localStorage.getItem('token')}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setPreviewAsset(asset);
        setPreviewHtml(data.html);
      }
    } catch {
      toast.error('Ошибка загрузки бирки');
    }
  };

  const previewBatch = async () => {
    if (selectedIds.size === 0) {
      toast.error('Выберите активы');
      return;
    }
    try {
      const ids = Array.from(selectedIds).join(',');
      const res = await fetch(`/api/marking/label-batch?asset_ids=${ids}`, {
        headers: localStorage.getItem('token') ? { 'Authorization': `Bearer ${localStorage.getItem('token')}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setBatchHtml(data.html);
        setShowBatchPreview(true);
      }
    } catch {
      toast.error('Ошибка загрузки пакетной бирки');
    }
  };

  const printBatch = () => {
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      toast.error('Блокировщик всплывающих окон');
      return;
    }
    printWindow.document.write(batchHtml);
    printWindow.document.close();
    printWindow.onload = () => {
      printWindow.print();
    };
  };

  const saveSettings = async () => {
    try {
      const res = await fetch('/api/marking/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(localStorage.getItem('token') ? { 'Authorization': `Bearer ${localStorage.getItem('token')}` } : {}),
        },
        body: JSON.stringify(settings),
      });
      if (res.ok) {
        toast.success('Настройки сохранены');
        setShowSettings(false);
      }
    } catch {
      toast.error('Ошибка сохранения');
    }
  };

  if (!canAccess) {
    return (
      <div className="text-center py-12">
        <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-200 mb-2">Доступ запрещён</h2>
        <p className="text-gray-600 dark:text-gray-400">У вас нет прав для доступа к разделу маркировки</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-200 flex items-center gap-3">
            <Tag className="w-8 h-8 text-blue-600" />
            Маркировка имущества
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Генерация и печать бирок для активов</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="flex items-center gap-2 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition"
          >
            <Settings className="w-4 h-4" />
            Настройки
          </button>
          <button
            onClick={previewBatch}
            disabled={selectedIds.size === 0}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <PrinterIcon className="w-4 h-4" />
            Печать ({selectedIds.size})
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Настройки маркировки
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Полное название фирмы
              </label>
              <input
                type="text"
                value={settings.company_name}
                onChange={e => setSettings({ ...settings, company_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                placeholder="ООО «ПАО»"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Сокращённое название
              </label>
              <input
                type="text"
                value={settings.company_short}
                onChange={e => setSettings({ ...settings, company_short: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                placeholder="ПАО"
              />
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <button
              onClick={saveSettings}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
            >
              Сохранить
            </button>
            <button
              onClick={() => setShowSettings(false)}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition"
            >
              Отмена
            </button>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4 border border-gray-200 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Поиск по названию, инв. номеру, ответственному..."
                className="w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
            </div>
          </div>
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          >
            <option value="">Все статусы</option>
            <option value="active">Активен</option>
            <option value="maintenance">На обслуживании</option>
            <option value="reserved">Зарезервирован</option>
            <option value="decommissioned">Снят с учёта</option>
          </select>
        </div>
      </div>

      {/* Assets Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-4 py-3 text-left">
                  <button onClick={selectAll} className="flex items-center gap-2 text-sm font-semibold text-gray-500 dark:text-gray-400">
                    {selectedIds.size === filteredAssets.length ? (
                      <CheckSquare className="w-5 h-5 text-blue-600" />
                    ) : (
                      <Square className="w-5 h-5 text-gray-400" />
                    )}
                  </button>
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                  Инв. номер
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                  Название
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                  Ответственный
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                  Дата постановки
                </th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                  Действия
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-500">
                    Загрузка...
                  </td>
                </tr>
              ) : filteredAssets.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-500">
                    Активы не найдены
                  </td>
                </tr>
              ) : (
                filteredAssets.map((asset) => (
                  <tr key={asset.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition">
                    <td className="px-4 py-3">
                      <button
                        onClick={() => toggleSelect(asset.id)}
                        className="flex items-center gap-2"
                      >
                        {selectedIds.has(asset.id) ? (
                          <CheckCircle2 className="w-5 h-5 text-green-600" />
                        ) : (
                          <Square className="w-5 h-5 text-gray-400" />
                        )}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-sm font-mono text-gray-800 dark:text-gray-200">
                      {asset.inventory_number}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-800 dark:text-gray-200">
                      {asset.name}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      {asset.responsible || '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      {asset.purchase_date ? new Date(asset.purchase_date).toLocaleDateString('ru-RU') : '—'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => previewSingle(asset)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700 transition"
                      >
                        <Eye className="w-3 h-3" />
                        Просмотр
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Single Label Preview Modal */}
      {previewAsset && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setPreviewAsset(null)}>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-lg w-full p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 mb-4">
              Предпросмотр бирки
            </h3>
            <div className="flex justify-center mb-4">
              <div
                dangerouslySetInnerHTML={{ __html: previewHtml }}
                className="max-w-full overflow-auto"
              />
            </div>
            <div className="text-center text-sm text-gray-600 dark:text-gray-400 mb-4">
              {previewAsset.name} | Инв. № {previewAsset.inventory_number}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setPreviewAsset(null)}
                className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Batch Preview Modal */}
      {showBatchPreview && batchHtml && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowBatchPreview(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-4xl w-full p-6 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
              <PrinterIcon className="w-5 h-5" />
              Пакетная печать бирок ({selectedIds.size} шт.)
            </h3>
            <div ref={printRef} className="mb-4">
              <div dangerouslySetInnerHTML={{ __html: batchHtml }} />
            </div>
            <div className="flex gap-2">
              <button
                onClick={printBatch}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                <PrinterIcon className="w-4 h-4" />
                Печать
              </button>
              <button
                onClick={() => setShowBatchPreview(false)}
                className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Marking;
