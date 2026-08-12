// frontend/src/pages/Marking.tsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import {
  Printer, Settings, CheckSquare, Square, Download,
  Tag, Search, Eye, Printer as PrinterIcon, CheckCircle2, XCircle, Upload, Image as ImageIcon, X
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
  logo_url: string | null;
}

const LABEL_SIZE_PRESETS = [
  { name: '105×37 мм', width: 105, height: 37, perRow: 3, perPage: 21 },
  { name: '100×40 мм', width: 100, height: 40, perRow: 3, perPage: 20 },
  { name: '99×38 мм', width: 99, height: 38, perRow: 3, perPage: 21 },
  { name: '90×45 мм', width: 90, height: 45, perRow: 3, perPage: 18 },
  { name: '100×50 мм', width: 100, height: 50, perRow: 2, perPage: 12 },
  { name: '65×40 мм', width: 65, height: 40, perRow: 4, perPage: 24 },
  { name: 'Custom', width: 0, height: 0, perRow: 0, perPage: 0 },
];

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
    logo_url: null,
  });
  const [showSettings, setShowSettings] = useState(false);
  const [activeSettingsTab, setActiveSettingsTab] = useState<'general' | 'labels' | 'logo'>('general');
  const [customWidth, setCustomWidth] = useState('');
  const [customHeight, setCustomHeight] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
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
        // Обновляем кастомные размеры если они есть
        if (data.label_width && data.label_height) {
          setCustomWidth(String(data.label_width));
          setCustomHeight(String(data.label_height));
        }
      }
    } catch {
      // Ignore
    }
  };

  const applyPreset = (preset: typeof LABEL_SIZE_PRESETS[0]) => {
    if (preset.name === 'Custom') {
      setActiveSettingsTab('labels');
      return;
    }
    setSettings(prev => ({
      ...prev,
      label_width: preset.width,
      label_height: preset.height,
      labels_per_row: preset.perRow,
      labels_per_page: preset.perPage,
    }));
    setCustomWidth(String(preset.width));
    setCustomHeight(String(preset.height));
    toast.success(`Применён пресет: ${preset.name}`);
  };

  const handleLogoUpload = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      toast.error('Можно загружать только изображения');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Файл слишком большой (макс. 5 МБ)');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', 'logo');

    try {
      const res = await fetch('/api/marking/logo-upload', {
        method: 'POST',
        headers: {
          ...(localStorage.getItem('token') ? { 'Authorization': `Bearer ${localStorage.getItem('token')}` } : {}),
        },
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        setSettings(prev => ({ ...prev, logo_url: data.url }));
        toast.success('Логотип загружен');
      } else {
        toast.error('Ошибка загрузки логотипа');
      }
    } catch {
      toast.error('Ошибка загрузки');
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleLogoUpload(file);
  }, []);

  const removeLogo = async () => {
    try {
      const res = await fetch('/api/marking/logo-upload', {
        method: 'DELETE',
        headers: {
          ...(localStorage.getItem('token') ? { 'Authorization': `Bearer ${localStorage.getItem('token')}` } : {}),
        },
      });
      if (res.ok) {
        setSettings(prev => ({ ...prev, logo_url: null }));
        toast.success('Логотип удалён');
      }
    } catch {
      toast.error('Ошибка удаления');
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
        (asset.responsible || '').toLowerCase().includes(s)
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
    const fullHtml = `
      <html>
      <head>
        <title>Бирки для печати</title>
        <style>
          @page { size: A4; margin: 5mm; }
          body { margin: 0; padding: 0; }
          .label { page-break-inside: avoid; }
          img { display: block; }
        </style>
      </head>
      <body>${batchHtml}</body>
      </html>
    `;
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      toast.error('Блокировщик всплывающих окон');
      return;
    }
    printWindow.document.write(fullHtml);
    printWindow.document.close();
    printWindow.onload = () => {
      printWindow.print();
    };
  };

  const printSingle = () => {
    if (!previewHtml || !previewAsset) return;
    const fullHtml = `
      <html>
      <head>
        <title>Бирка — ${previewAsset.inventory_number}</title>
        <style>
          @page { margin: 0; size: auto; }
          body { margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
          .label { page-break-inside: avoid; }
          img { display: block; }
        </style>
      </head>
      <body>${previewHtml}</body>
      </html>
    `;
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      toast.error('Блокировщик всплывающих окон');
      return;
    }
    printWindow.document.write(fullHtml);
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
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700">
          {/* Tabs */}
          <div className="border-b border-gray-200 dark:border-gray-700">
            <div className="flex">
              <button
                onClick={() => setActiveSettingsTab('general')}
                className={`px-4 py-3 text-sm font-medium transition ${
                  activeSettingsTab === 'general'
                    ? 'border-b-2 border-blue-600 text-blue-600 dark:text-blue-400'
                    : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                📝 Общие
              </button>
              <button
                onClick={() => setActiveSettingsTab('labels')}
                className={`px-4 py-3 text-sm font-medium transition ${
                  activeSettingsTab === 'labels'
                    ? 'border-b-2 border-blue-600 text-blue-600 dark:text-blue-400'
                    : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                📐 Размеры бирок
              </button>
              <button
                onClick={() => setActiveSettingsTab('logo')}
                className={`px-4 py-3 text-sm font-medium transition ${
                  activeSettingsTab === 'logo'
                    ? 'border-b-2 border-blue-600 text-blue-600 dark:text-blue-400'
                    : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                🖼️ Логотип
              </button>
            </div>
          </div>

          <div className="p-6">
            {/* General Tab */}
            {activeSettingsTab === 'general' && (
              <div className="space-y-4">
                <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  Общие настройки
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
              </div>
            )}

            {/* Label Size Tab */}
            {activeSettingsTab === 'labels' && (
              <div className="space-y-6">
                <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  Размеры бирок
                </h3>

                {/* Presets */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Готовые пресеты
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    {LABEL_SIZE_PRESETS.filter(p => p.name !== 'Custom').map((preset) => (
                      <button
                        key={preset.name}
                        onClick={() => applyPreset(preset)}
                        className={`px-3 py-2 rounded-lg border-2 transition text-sm font-medium ${
                          settings.label_width === preset.width && settings.label_height === preset.height
                            ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                            : 'border-gray-200 dark:border-gray-600 hover:border-blue-400 text-gray-700 dark:text-gray-300'
                        }`}
                      >
                        {preset.name}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Custom dimensions */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Свой размер (мм)
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Ширина</label>
                      <input
                        type="number"
                        value={customWidth}
                        onChange={e => {
                          setCustomWidth(e.target.value);
                          setSettings(prev => ({ ...prev, label_width: Number(e.target.value) }));
                        }}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        placeholder="105"
                        min={30}
                        max={210}
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Высота</label>
                      <input
                        type="number"
                        value={customHeight}
                        onChange={e => {
                          setCustomHeight(e.target.value);
                          setSettings(prev => ({ ...prev, label_height: Number(e.target.value) }));
                        }}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        placeholder="37"
                        min={10}
                        max={100}
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">На строку</label>
                      <input
                        type="number"
                        value={settings.labels_per_row}
                        onChange={e => setSettings(prev => ({ ...prev, labels_per_row: Number(e.target.value) }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        min={1}
                        max={10}
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">На страницу</label>
                      <input
                        type="number"
                        value={settings.labels_per_page}
                        onChange={e => setSettings(prev => ({ ...prev, labels_per_page: Number(e.target.value) }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        min={1}
                        max={100}
                      />
                    </div>
                  </div>
                </div>

                {/* Visual preview */}
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Визуализация:</p>
                  <div className="flex items-center justify-center">
                    <div
                      className="border-2 border-dashed border-gray-400 rounded flex items-center justify-center text-gray-500 dark:text-gray-400 text-xs"
                      style={{
                        width: `${Math.min(settings.label_width * 3, 200)}px`,
                        height: `${Math.min(settings.label_height * 3, 100)}px`,
                      }}
                    >
                      {settings.label_width}×{settings.label_height} мм
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Logo Tab */}
            {activeSettingsTab === 'logo' && (
              <div className="space-y-4">
                <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 flex items-center gap-2">
                  <ImageIcon className="w-5 h-5" />
                  Логотип компании
                </h3>

                {!settings.logo_url ? (
                  <div
                    onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition ${
                      isDragging
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-300 dark:border-gray-600 hover:border-blue-400'
                    }`}
                  >
                    <Upload className="w-12 h-12 mx-auto text-gray-400 mb-3" />
                    <p className="text-gray-600 dark:text-gray-400 font-medium mb-1">
                      Перетащите изображение сюда
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-500 mb-3">
                      или нажмите для выбора файла
                    </p>
                    <p className="text-xs text-gray-400 dark:text-gray-500">
                      PNG, JPG, SVG до 5 МБ
                    </p>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) handleLogoUpload(file);
                      }}
                    />
                  </div>
                ) : (
                  <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0 p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600">
                        <img
                          src={settings.logo_url}
                          alt="Логотип"
                          className="w-24 h-24 object-contain"
                        />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
                          Логотип загружен
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                          Логотип будет отображаться на всех бирках
                        </p>
                        <button
                          onClick={removeLogo}
                          className="flex items-center gap-2 px-3 py-1.5 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 transition"
                        >
                          <X className="w-4 h-4" />
                          Удалить логотип
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Save buttons */}
            <div className="flex gap-2 mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={saveSettings}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
              >
                💾 Сохранить
              </button>
              <button
                onClick={() => {
                  setShowSettings(false);
                  setActiveSettingsTab('general');
                }}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition"
              >
                Отмена
              </button>
            </div>
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
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-2xl w-full p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 mb-4">
              Предпросмотр бирки
            </h3>
            <div className="flex justify-center mb-4 overflow-auto max-h-[60vh] p-4 bg-gray-50 dark:bg-gray-900 rounded-lg" style={{ minHeight: '200px' }}>
              <div
                dangerouslySetInnerHTML={{ __html: previewHtml }}
              />
            </div>
            <div className="text-center text-sm text-gray-600 dark:text-gray-400 mb-4">
              {previewAsset.name} | Инв. № {previewAsset.inventory_number}
            </div>
            <div className="flex gap-2">
              <button
                onClick={printSingle}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                <PrinterIcon className="w-4 h-4" />
                Печать
              </button>
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
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-6xl w-full p-6 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
              <PrinterIcon className="w-5 h-5" />
              Пакетная печать бирок ({selectedIds.size} шт.)
            </h3>
            <div ref={printRef} className="mb-4 bg-gray-50 dark:bg-gray-900 rounded-lg p-4" style={{ minHeight: '200px', overflow: 'auto', maxHeight: '70vh' }}>
              <div
                dangerouslySetInnerHTML={{ __html: batchHtml.replace(/<\/?html[^>]*>/g, '').replace(/<\/?head[^>]*>/g, '').replace(/<\/?body[^>]*>/g, '').replace(/<title>[^<]*<\/title>/gi, '') }}
                style={{ display: 'flex', flexWrap: 'wrap', gap: '1mm', justifyContent: 'center' }}
              />
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
