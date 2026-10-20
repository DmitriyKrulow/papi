// frontend/src/pages/Marking.tsx
import React, { useState, useEffect, useRef, useCallback, useLayoutEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import {
  Printer, Settings, CheckSquare, Square,
  Tag, Search, Eye, Printer as PrinterIcon, CheckCircle2, XCircle, Upload, Image as ImageIcon, X,
  ZoomIn, ZoomOut, Maximize,
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

interface BatchResult {
  labels: string[];
  count: number;
  label_width: number;
  label_height: number;
  labels_per_row: number;
  labels_per_page: number;
}

const LABEL_SIZE_PRESETS = [
  { name: '105×37 мм', width: 105, height: 37 },
  { name: '100×40 мм', width: 100, height: 40 },
  { name: '99×38 мм', width: 99, height: 38 },
  { name: '90×45 мм', width: 90, height: 45 },
  { name: '100×50 мм', width: 100, height: 50 },
  { name: '80×40 мм', width: 80, height: 40 },
  { name: '70×35 мм', width: 70, height: 35 },
  { name: '65×40 мм', width: 65, height: 40 },
  { name: '50×25 мм', width: 50, height: 25 },
];

// A4 лист и поля печати
const PAGE_W = 210;
const PAGE_H = 297;
const PAGE_MARGIN = 5;
// Пикселей в одном миллиметре при 96dpi
const MM = 96 / 25.4;

/** Делает относительные URL абсолютными (для iframe и окна печати). */
const absolutize = (html: string) =>
  html.replace(/src="\//g, `src="${window.location.origin}/`);

/** Собирает полный HTML-документ для печати. */
const buildPrintDoc = (
  labels: string[],
  opts: { width: number; height: number; perRow: number; single?: boolean },
) => {
  const page = opts.single
    ? `${opts.width}mm ${opts.height}mm`
    : 'A4';
  const margin = opts.single ? 0 : PAGE_MARGIN;
  return `<!doctype html><html><head><meta charset="utf-8"><title>Бирки</title><style>
@page { size: ${page}; margin: ${margin}mm; }
html, body { margin: 0; padding: 0; background: #fff; }
body { display: grid; grid-template-columns: repeat(${opts.perRow}, ${opts.width}mm); justify-content: center; align-content: start; }
.papi-label { page-break-inside: avoid; break-inside: avoid; }
</style></head><body>${absolutize(labels.join(''))}</body></html>`;
};

/** Хук: масштаб, при котором содержимое размером wmm×hmm целиком влезает в контейнер. */
const useFitZoom = (wmm: number, hmm: number) => {
  const ref = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState(1);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const update = () => {
      const availW = el.clientWidth - 24;
      const availH = el.clientHeight - 24;
      if (availW <= 0 || availH <= 0) return;
      const z = Math.min(availW / (wmm * MM), availH / (hmm * MM), 2);
      setZoom(Math.max(0.1, z));
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, [wmm, hmm]);

  return { ref, zoom };
};

/** Рамка, которая рендерит HTML в изолированном iframe и масштабирует его. */
const ScaledFrame: React.FC<{
  html: string;
  wmm: number;
  hmm: number;
  zoom: number;
  title?: string;
}> = ({ html, wmm, hmm, zoom, title }) => (
  <div
    style={{
      width: wmm * MM * zoom,
      height: hmm * MM * zoom,
      flex: '0 0 auto',
      position: 'relative',
    }}
  >
    <iframe
      title={title}
      srcDoc={html}
      scrolling="no"
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: wmm * MM,
        height: hmm * MM,
        border: 0,
        background: '#fff',
        transform: `scale(${zoom})`,
        transformOrigin: '0 0',
      }}
    />
  </div>
);

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

  // Одиночный предпросмотр
  const [previewAsset, setPreviewAsset] = useState<MarkingAsset | null>(null);
  const [previewHtml, setPreviewHtml] = useState('');
  const [previewSize, setPreviewSize] = useState({ width: 105, height: 37 });
  const [previewZoom, setPreviewZoom] = useState(1);
  const [previewFit, setPreviewFit] = useState(true);
  const singlePreview = useFitZoom(previewSize.width, previewSize.height);

  // Пакетный предпросмотр
  const [batch, setBatch] = useState<BatchResult | null>(null);
  const [showBatchPreview, setShowBatchPreview] = useState(false);
  const [batchZoom, setBatchZoom] = useState(1);
  const [batchFit, setBatchFit] = useState(true);
  const batchPreview = useFitZoom(PAGE_W, PAGE_H);

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
    setSettings(prev => ({
      ...prev,
      label_width: preset.width,
      label_height: preset.height,
    }));
    setCustomWidth(String(preset.width));
    setCustomHeight(String(preset.height));
    toast.success(`Применён пресет: ${preset.name}`);
  };

  /** Вычисляет рекомендаемую раскладку для A4 (поля 5 мм). */
  const calcLayout = (w: number, h: number) => {
    const usableW = PAGE_W - 2 * PAGE_MARGIN;
    const usableH = PAGE_H - 2 * PAGE_MARGIN;
    const perRow = Math.max(1, Math.floor(usableW / w));
    const rows = Math.max(1, Math.floor(usableH / h));
    return { perRow, perPage: perRow * rows };
  };

  const previewSingle = async (asset: MarkingAsset) => {
    try {
      const res = await fetch(`/api/marking/label-html/${asset.id}`, {
        headers: localStorage.getItem('token') ? { 'Authorization': `Bearer ${localStorage.getItem('token')}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setPreviewAsset(asset);
        setPreviewHtml(data.html);
        setPreviewSize({ width: data.label_width, height: data.label_height });
        setPreviewFit(true);
        setPreviewZoom(1);
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
        const data = await res.json() as BatchResult;
        setBatch(data);
        setBatchFit(true);
        setBatchZoom(1);
        setShowBatchPreview(true);
      }
    } catch {
      toast.error('Ошибка загрузки пакетной бирки');
    }
  };

  const printBatch = () => {
    if (!batch) return;
    const { width, height, labels_per_row } = batch;
    const fullHtml = buildPrintDoc(batch.labels, { width, height, perRow: labels_per_row });
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
    const { width, height } = previewSize;
    const fullHtml = buildPrintDoc([previewHtml], { width, height, perRow: 1, single: true });
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
      {previewAsset && (() => {
        const { width: lw, height: lh } = previewSize;
        const effZoom = previewFit ? singlePreview.zoom : previewZoom;
        const doc = buildPrintDoc([previewHtml], { width: lw, height: lh, perRow: 1, single: true });
        return (
          <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setPreviewAsset(null)}>
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-3xl flex flex-col max-h-[90vh]" onClick={e => e.stopPropagation()}>
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200">Предпросмотр бирки</h3>
                <button onClick={() => setPreviewAsset(null)} className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500">
                  <X className="w-5 h-5" />
                </button>
              </div>
              {/* Preview area */}
              <div
                ref={singlePreview.ref}
                className="flex-1 overflow-auto flex items-center justify-center p-6"
                style={{ background: '#e5e7eb', minHeight: '200px' }}
              >
                <div style={{ boxShadow: '0 4px 24px rgba(0,0,0,.18)', borderRadius: '2px' }}>
                  <ScaledFrame html={doc} wmm={lw} hmm={lh} zoom={effZoom} title={`Бирка ${previewAsset.inventory_number}`} />
                </div>
              </div>
              {/* Zoom controls */}
              <div className="flex items-center gap-2 px-6 py-2 border-t border-gray-200 dark:border-gray-700 text-sm text-gray-600 dark:text-gray-400">
                <button onClick={() => { setPreviewZoom(z => Math.max(0.2, z - 0.15)); setPreviewFit(false); }} className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"><ZoomOut className="w-4 h-4" /></button>
                <span className="w-12 text-center">{Math.round(effZoom * 100)}%</span>
                <button onClick={() => { setPreviewZoom(z => Math.min(3, z + 0.15)); setPreviewFit(false); }} className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"><ZoomIn className="w-4 h-4" /></button>
                <button onClick={() => setPreviewFit(true)} className={`ml-2 p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 ${previewFit ? 'text-blue-600' : ''}`} title="По размеру"><Maximize className="w-4 h-4" /></button>
                <span className="ml-auto text-xs">{lw}×{lh} мм</span>
              </div>
              {/* Info + actions */}
              <div className="px-6 pb-5">
                <p className="text-center text-sm text-gray-600 dark:text-gray-400 mb-4 truncate">
                  {previewAsset.name} | Инв. № {previewAsset.inventory_number}
                </p>
                <div className="flex gap-2">
                  <button onClick={printSingle} className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium">
                    <PrinterIcon className="w-4 h-4" /> Печать
                  </button>
                  <button onClick={() => setPreviewAsset(null)} className="flex-1 px-4 py-2.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition">
                    Закрыть
                  </button>
                </div>
              </div>
            </div>
          </div>
        );
      })()}

      {/* Batch Preview Modal */}
      {showBatchPreview && batch && (() => {
        const { labels, label_width: lw, label_height: lh, labels_per_row: perRow, labels_per_page: perPage } = batch;
        const effZoom = batchFit ? batchPreview.zoom : batchZoom;
        const pages: string[][] = [];
        for (let i = 0; i < labels.length; i += perPage) {
          pages.push(labels.slice(i, i + perPage));
        }
        return (
          <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setShowBatchPreview(false)}>
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-5xl flex flex-col max-h-[90vh]" onClick={e => e.stopPropagation()}>
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 flex items-center gap-2">
                  <PrinterIcon className="w-5 h-5" />
                  Пакетная печать ({labels.length} шт., {pages.length} лист.)
                </h3>
                <button onClick={() => setShowBatchPreview(false)} className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500">
                  <X className="w-5 h-5" />
                </button>
              </div>
              {/* Pages preview */}
              <div
                ref={batchPreview.ref}
                className="flex-1 overflow-auto flex flex-col items-center gap-4 p-6"
                style={{ background: '#e5e7eb' }}
              >
                {pages.map((pageLabels, i) => {
                  const doc = buildPrintDoc(pageLabels, { width: lw, height: lh, perRow });
                  return (
                    <div key={i} className="flex flex-col items-center gap-1">
                      <div style={{ boxShadow: '0 4px 24px rgba(0,0,0,.18)', borderRadius: '2px' }}>
                        <ScaledFrame html={doc} wmm={PAGE_W} hmm={PAGE_H} zoom={effZoom} title={`Лист ${i + 1}`} />
                      </div>
                      <span className="text-xs text-gray-500">Лист {i + 1} / {pages.length}</span>
                    </div>
                  );
                })}
              </div>
              {/* Zoom controls */}
              <div className="flex items-center gap-2 px-6 py-2 border-t border-gray-200 dark:border-gray-700 text-sm text-gray-600 dark:text-gray-400">
                <button onClick={() => { setBatchZoom(z => Math.max(0.1, z - 0.1)); setBatchFit(false); }} className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"><ZoomOut className="w-4 h-4" /></button>
                <span className="w-12 text-center">{Math.round(effZoom * 100)}%</span>
                <button onClick={() => { setBatchZoom(z => Math.min(2, z + 0.1)); setBatchFit(false); }} className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"><ZoomIn className="w-4 h-4" /></button>
                <button onClick={() => setBatchFit(true)} className={`ml-2 p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 ${batchFit ? 'text-blue-600' : ''}`} title="По размеру"><Maximize className="w-4 h-4" /></button>
                <span className="ml-auto text-xs">{lw}×{lh} мм · {perRow}/ряд · {perPage}/лист</span>
              </div>
              {/* Actions */}
              <div className="px-6 pb-5 pt-2">
                <div className="flex gap-2">
                  <button onClick={printBatch} className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium">
                    <PrinterIcon className="w-4 h-4" /> Печать
                  </button>
                  <button onClick={() => setShowBatchPreview(false)} className="flex-1 px-4 py-2.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition">
                    Закрыть
                  </button>
                </div>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};

export default Marking;
