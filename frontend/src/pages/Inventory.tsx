// frontend/src/pages/Inventory.tsx
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import {
  ClipboardList, Plus, Trash2, Play, CheckCircle2, XCircle,
  Download, QrCode, Search, ChevronRight, ChevronLeft,
  Building2, User, Users, Package, AlertTriangle, RefreshCw,
  Check, X, Clock, FileText, Printer
} from 'lucide-react';
import toast from 'react-hot-toast';

// ====================== ТИПЫ ======================

interface InventoryCheckItem {
  id: number;
  asset_id: number;
  inventory_number: string;
  asset_name: string;
  asset_type: string;
  model: string;
  location: string;
  responsible: string;
  result: 'pending' | 'found' | 'missing';
  comment: string | null;
  confirmed_by: string | null;
  confirmed_at: string | null;
}

interface InventoryCheck {
  id: number;
  name: string;
  check_date: string;
  check_type: 'full' | 'by_room' | 'by_employee' | 'by_responsible';
  scope_id: number | null;
  scope_name: string | null;
  department_id: number | null;
  department_name: string | null;
  total_checked: number;
  found: number;
  missing: number;
  surplus: number;
  status: 'draft' | 'in_progress' | 'completed' | 'cancelled';
  responsible_name: string | null;
  creator_name: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  items?: InventoryCheckItem[];
  commission_members?: string | null;
}

interface ScopeOption {
  id: number;
  name: string;
  department_id?: number;
  building?: string;
  floor?: string;
  position?: string;
  type?: string;
  role?: string;
  username?: string;
}

// ====================== ВСПОМОГАТЕЛЬНЫЕ ======================

const TYPE_LABELS: Record<string, string> = {
  full: 'Полная инвентаризация',
  by_room: 'По помещению',
  by_employee: 'По сотруднику',
  by_responsible: 'По ответственному',
};

const TYPE_ICONS: Record<string, React.ReactNode> = {
  full: <Package className="w-4 h-4" />,
  by_room: <Building2 className="w-4 h-4" />,
  by_employee: <User className="w-4 h-4" />,
  by_responsible: <Users className="w-4 h-4" />,
};

const STATUS_LABELS: Record<string, string> = {
  draft: 'Черновик',
  in_progress: 'В процессе',
  completed: 'Завершена',
  cancelled: 'Отменена',
};

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  in_progress: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
  cancelled: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
};

// ====================== ОСНОВНОЙ КОМПОНЕНТ ======================

const Inventory: React.FC = () => {
  const { isAdmin, user } = useAuth();
  const [checks, setChecks] = useState<InventoryCheck[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCheck, setSelectedCheck] = useState<InventoryCheck | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showQrModal, setShowQrModal] = useState<InventoryCheck | null>(null);

  const fetchChecks = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/inventory-checks', {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setChecks(data);
      } else {
        toast.error('Ошибка загрузки списка');
      }
    } catch {
      toast.error('Ошибка соединения');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchChecks();
  }, [fetchChecks]);

  const fetchCheckDetails = async (checkId: number) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/inventory-checks/${checkId}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedCheck(data);
      }
    } catch {
      toast.error('Ошибка загрузки деталей');
    }
  };

  const handleStart = async (checkId: number) => {
    if (!confirm('Начать инвентаризацию? Это сбросит статус проверки у всех активов.')) return;
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/inventory-checks/${checkId}/start`, {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(data.message);
        fetchChecks();
        fetchCheckDetails(checkId);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Ошибка');
      }
    } catch {
      toast.error('Ошибка соединения');
    }
  };

  const handleComplete = async (checkId: number) => {
    if (!confirm('Завершить инвентаризацию?')) return;
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/inventory-checks/${checkId}/complete`, {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(data.message);
        fetchChecks();
        fetchCheckDetails(checkId);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Ошибка');
      }
    } catch {
      toast.error('Ошибка соединения');
    }
  };

  const handleDelete = async (checkId: number) => {
    if (!confirm('Удалить инвентаризацию? Это действие необратимо.')) return;
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/inventory-checks/${checkId}`, {
        method: 'DELETE',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      });
      if (res.ok) {
        toast.success('Инвентаризация удалена');
        setSelectedCheck(null);
        fetchChecks();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Ошибка');
      }
    } catch {
      toast.error('Ошибка соединения');
    }
  };

  const handleConfirm = async (checkId: number, assetId: number, found: boolean) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(
        `/api/inventory-checks/${checkId}/confirm/${assetId}?found=${found}`,
        { method: 'POST', headers: token ? { 'Authorization': `Bearer ${token}` } : {} }
      );
      if (res.ok) {
        fetchCheckDetails(checkId);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Ошибка');
      }
    } catch {
      toast.error('Ошибка соединения');
    }
  };

  const handleResetAsset = async (checkId: number, assetId: number) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(
        `/api/inventory-checks/${checkId}/reset-asset/${assetId}`,
        { method: 'POST', headers: token ? { 'Authorization': `Bearer ${token}` } : {} }
      );
      if (res.ok) {
        toast.success('Статус сброшен');
        fetchCheckDetails(checkId);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Ошибка');
      }
    } catch {
      toast.error('Ошибка соединения');
    }
  };

  // ====================== РЕНДЕР ======================

  if (loading) {
    return (
      <div className="flex justify-center items-center py-16">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <ClipboardList className="w-7 h-7 text-blue-600" />
            Инвентаризация
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Сверка имущества по помещениям, сотрудникам и ответственным лицам
          </p>
        </div>
        {isAdmin && (
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition"
          >
            <Plus className="w-4 h-4" />
            Создать инвентаризацию
          </button>
        )}
      </div>

      {/* List view */}
      {!selectedCheck && (
        <>
          {checks.length === 0 ? (
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-8 text-center">
              <ClipboardList className="w-12 h-12 text-blue-400 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-200 mb-2">Нет инвентаризаций</h3>
              <p className="text-blue-700 dark:text-blue-300 text-sm">
                {isAdmin
                  ? 'Создайте первую инвентаризацию для сверки имущества'
                  : 'Инвентаризации пока не созданы'}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {checks.map((check) => (
                <div
                  key={check.id}
                  className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:shadow-md transition cursor-pointer"
                  onClick={() => fetchCheckDetails(check.id)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
                        {TYPE_ICONS[check.check_type]}
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100">{check.name}</h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {TYPE_LABELS[check.check_type]}
                          {check.scope_name ? ` • ${check.scope_name}` : ''}
                        </p>
                      </div>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[check.status]}`}>
                      {STATUS_LABELS[check.status]}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-center mb-3">
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2">
                      <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{check.total_checked}</p>
                      <p className="text-xs text-gray-500">Всего</p>
                    </div>
                    <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-2">
                      <p className="text-lg font-bold text-green-600 dark:text-green-400">{check.found}</p>
                      <p className="text-xs text-gray-500">Найдено</p>
                    </div>
                    <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-2">
                      <p className="text-lg font-bold text-red-600 dark:text-red-400">{check.missing}</p>
                      <p className="text-xs text-gray-500">Отсутствует</p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-xs text-gray-400 dark:text-gray-500">
                    <span>{check.creator_name || '—'}</span>
                    <span>{check.created_at ? new Date(check.created_at).toLocaleDateString('ru-RU') : '—'}</span>
                  </div>

                  <div className="mt-3 flex gap-2">
                    <button
                      onClick={(e) => { e.stopPropagation(); fetchCheckDetails(check.id); }}
                      className="flex-1 px-3 py-1.5 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center justify-center gap-1"
                    >
                      <ChevronRight className="w-3.5 h-3.5" /> Открыть
                    </button>
                    {check.status === 'in_progress' && (
                      <button
                        onClick={(e) => { e.stopPropagation(); setShowQrModal(check); }}
                        className="px-3 py-1.5 text-xs border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition flex items-center gap-1"
                      >
                        <QrCode className="w-3.5 h-3.5" /> QR
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Detail view */}
      {selectedCheck && (
        <CheckDetailView
          check={selectedCheck}
          isAdmin={isAdmin}
          onBack={() => { setSelectedCheck(null); fetchChecks(); }}
          onStart={handleStart}
          onComplete={handleComplete}
          onDelete={handleDelete}
          onConfirm={handleConfirm}
          onResetAsset={handleResetAsset}
          onRefresh={() => fetchCheckDetails(selectedCheck.id)}
          onShowQr={() => setShowQrModal(selectedCheck)}
        />
      )}

      {/* Create modal */}
      {showCreateModal && (
        <CreateCheckModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => { setShowCreateModal(false); fetchChecks(); }}
        />
      )}

      {/* QR modal */}
      {showQrModal && (
        <QrModal check={showQrModal} onClose={() => setShowQrModal(null)} />
      )}
    </div>
  );
};

// ====================== ДЕТАЛИ ИНВЕНТАРИЗАЦИИ ======================

interface CheckDetailViewProps {
  check: InventoryCheck;
  isAdmin: boolean;
  onBack: () => void;
  onStart: (id: number) => void;
  onComplete: (id: number) => void;
  onDelete: (id: number) => void;
  onConfirm: (checkId: number, assetId: number, found: boolean) => void;
  onResetAsset: (checkId: number, assetId: number) => void;
  onRefresh: () => void;
  onShowQr: () => void;
}

const CheckDetailView: React.FC<CheckDetailViewProps> = ({
  check, isAdmin, onBack, onStart, onComplete, onDelete, onConfirm, onResetAsset, onRefresh, onShowQr
}) => {
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'pending' | 'found' | 'missing'>('all');

  const items = check.items || [];
  const filtered = items.filter(item => {
    if (filter !== 'all' && item.result !== filter) return false;
    if (search) {
      const s = search.toLowerCase();
      return item.inventory_number.toLowerCase().includes(s) ||
             item.asset_name.toLowerCase().includes(s) ||
             item.location.toLowerCase().includes(s);
    }
    return true;
  });

  const pendingCount = items.filter(i => i.result === 'pending').length;
  const foundCount = items.filter(i => i.result === 'found').length;
  const missingCount = items.filter(i => i.result === 'missing').length;
  const progress = items.length > 0 ? ((foundCount + missingCount) / items.length * 100).toFixed(0) : '0';

  return (
    <div className="space-y-4">
      {/* Top bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition"
        >
          <ChevronLeft className="w-4 h-4" /> Назад к списку
        </button>

        <div className="flex gap-2 flex-wrap">
          {isAdmin && check.status === 'draft' && (
            <button
              onClick={() => onStart(check.id)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 transition"
            >
              <Play className="w-4 h-4" /> Начать
            </button>
          )}
          {isAdmin && check.status === 'in_progress' && (
            <>
              <button
                onClick={onShowQr}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 text-sm rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
              >
                <QrCode className="w-4 h-4" /> QR-код
              </button>
              <button
                onClick={() => onComplete(check.id)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition"
              >
                <CheckCircle2 className="w-4 h-4" /> Завершить
              </button>
            </>
          )}
          {isAdmin && (check.status === 'draft' || check.status === 'cancelled') && (
            <button
              onClick={() => onDelete(check.id)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-50 text-red-600 dark:bg-red-900/20 dark:text-red-400 text-sm rounded-lg hover:bg-red-100 dark:hover:bg-red-900/40 transition"
            >
              <Trash2 className="w-4 h-4" /> Удалить
            </button>
          )}
        </div>
      </div>

      {/* Info card */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              {TYPE_ICONS[check.check_type]}
              {check.name}
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {TYPE_LABELS[check.check_type]}
              {check.scope_name ? ` • ${check.scope_name}` : ''}
              {check.department_name ? ` • ${check.department_name}` : ''}
            </p>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${STATUS_COLORS[check.status]}`}>
            {STATUS_LABELS[check.status]}
          </span>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{check.total_checked}</p>
            <p className="text-xs text-gray-500">Всего активов</p>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">{foundCount}</p>
            <p className="text-xs text-gray-500">Найдено</p>
          </div>
          <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-red-600 dark:text-red-400">{missingCount}</p>
            <p className="text-xs text-gray-500">Отсутствует</p>
          </div>
          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{pendingCount}</p>
            <p className="text-xs text-gray-500">Осталось проверить</p>
          </div>
        </div>

        {/* Progress bar */}
        {check.status === 'in_progress' && (
          <div className="mb-2">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>Прогресс проверки</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full bg-gray-100 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
              <div
                className="h-full bg-blue-600 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Meta info */}
        <div className="flex flex-wrap gap-4 text-xs text-gray-400 dark:text-gray-500">
          <span>Создал: {check.creator_name || '—'}</span>
          <span>Дата: {check.check_date ? new Date(check.check_date).toLocaleDateString('ru-RU') : '—'}</span>
          {check.started_at && <span>Начата: {new Date(check.started_at).toLocaleString('ru-RU')}</span>}
          {check.completed_at && <span>Завершена: {new Date(check.completed_at).toLocaleString('ru-RU')}</span>}
        </div>
      </div>

      {/* Items */}
      {check.status === 'in_progress' || check.status === 'completed' ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          {/* Filters */}
          <div className="flex flex-wrap gap-3 mb-4">
            <div className="flex-1 min-w-[200px] relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Поиск по инв. номеру, названию, кабинету..."
                className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex gap-1">
              {(['all', 'pending', 'found', 'missing'] as const).map(f => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-3 py-1.5 text-xs rounded-lg transition ${
                    filter === f
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  {f === 'all' ? 'Все' : f === 'pending' ? 'Ожидают' : f === 'found' ? 'Найдены' : 'Отсутствуют'}
                </button>
              ))}
            </div>
          </div>

          {/* Items list */}
          {filtered.length === 0 ? (
            <p className="text-center text-gray-400 py-8">Нет активов для отображения</p>
          ) : (
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
              {filtered.map(item => (
                <div
                  key={item.id}
                  className={`flex items-center gap-3 p-3 rounded-lg border transition ${
                    item.result === 'found'
                      ? 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/10'
                      : item.result === 'missing'
                      ? 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10'
                      : 'border-gray-200 dark:border-gray-700'
                  }`}
                >
                  <div className="flex-shrink-0">
                    {item.result === 'found' ? (
                      <CheckCircle2 className="w-5 h-5 text-green-500" />
                    ) : item.result === 'missing' ? (
                      <XCircle className="w-5 h-5 text-red-500" />
                    ) : (
                      <Clock className="w-5 h-5 text-gray-400" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-gray-500">{item.inventory_number}</span>
                      <span className="font-medium text-gray-900 dark:text-gray-100 truncate">{item.asset_name}</span>
                    </div>
                    <div className="text-xs text-gray-400 dark:text-gray-500 flex flex-wrap gap-2 mt-0.5">
                      {item.model && <span>{item.model}</span>}
                      {item.location && <span>📍 {item.location}</span>}
                      {item.responsible && <span>👤 {item.responsible}</span>}
                      {item.confirmed_by && <span>✓ {item.confirmed_by}</span>}
                    </div>
                  </div>

                  {/* Action buttons */}
                  <div className="flex-shrink-0 flex gap-1">
                    {check.status === 'in_progress' && (
                      <>
                        {item.result !== 'found' && (
                          <button
                            onClick={() => onConfirm(check.id, item.asset_id, true)}
                            className="px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 transition flex items-center gap-1"
                            title="Найден"
                          >
                            <Check className="w-3.5 h-3.5" /> Найден
                          </button>
                        )}
                        {item.result !== 'missing' && (
                          <button
                            onClick={() => onConfirm(check.id, item.asset_id, false)}
                            className="px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition flex items-center gap-1"
                            title="Отсутствует"
                          >
                            <X className="w-3.5 h-3.5" /> Нет
                          </button>
                        )}
                        {isAdmin && item.result !== 'pending' && (
                          <button
                            onClick={() => onResetAsset(check.id, item.asset_id)}
                            className="px-2 py-1 text-xs border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition flex items-center gap-1"
                            title="Сбросить (админ)"
                          >
                            <RefreshCw className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </>
                    )}
                    {check.status === 'completed' && isAdmin && (
                      <button
                        onClick={() => onResetAsset(check.id, item.asset_id)}
                        className="px-2 py-1 text-xs border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition flex items-center gap-1"
                        title="Сбросить (админ)"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-8 text-center">
          <FileText className="w-10 h-10 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-500 dark:text-gray-400">
            {check.status === 'draft'
              ? 'Инвентаризация ещё не начата. Нажмите "Начать" для запуска проверки.'
              : 'Инвентаризация отменена'}
          </p>
        </div>
      )}
    </div>
  );
};

// ====================== МОДАЛКА СОЗДАНИЯ ======================

interface CreateCheckModalProps {
  onClose: () => void;
  onCreated: () => void;
}

const CreateCheckModal: React.FC<CreateCheckModalProps> = ({ onClose, onCreated }) => {
  const [name, setName] = useState('');
  const [checkDate, setCheckDate] = useState(new Date().toISOString().slice(0, 10));
  const [checkType, setCheckType] = useState<'full' | 'by_room' | 'by_employee' | 'by_responsible'>('full');
  const [scopeId, setScopeId] = useState<number | null>(null);
  const [scopeOptions, setScopeOptions] = useState<ScopeOption[]>([]);
  const [loadingScope, setLoadingScope] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (checkType !== 'full') {
      setLoadingScope(true);
      fetch(`/api/inventory-checks/scope-options?check_type=${checkType}`)
        .then(res => res.json())
        .then(data => {
          setScopeOptions(Array.isArray(data) ? data : []);
          setLoadingScope(false);
        })
        .catch(() => { setScopeOptions([]); setLoadingScope(false); });
    } else {
      setScopeOptions([]);
      setScopeId(null);
    }
  }, [checkType]);

  const handleSubmit = async () => {
    if (!name.trim()) { toast.error('Введите название'); return; }
    if (checkType !== 'full' && !scopeId) { toast.error('Выберите объект проверки'); return; }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        name: name.trim(),
        check_date: checkDate,
        check_type: checkType,
      });
      if (scopeId) {
        params.append('scope_id', String(scopeId));
        const opt = scopeOptions.find(o => o.id === scopeId);
        if (opt) params.append('scope_name', opt.name);
      }

      const res = await fetch(`/api/inventory-checks?${params.toString()}`, {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      });

      if (res.ok) {
        toast.success('Инвентаризация создана');
        onCreated();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Ошибка создания');
      }
    } catch {
      toast.error('Ошибка соединения');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
          <Plus className="w-5 h-5 text-blue-600" />
          Новая инвентаризация
        </h3>

        <div className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Название</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Например: Инвентаризация 2026"
              className="w-full px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Дата проверки</label>
            <input
              type="date"
              value={checkDate}
              onChange={(e) => setCheckDate(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Тип проверки</label>
            <select
              value={checkType}
              onChange={(e) => setCheckType(e.target.value as any)}
              className="w-full px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="full">Полная (все активы)</option>
              <option value="by_room">По помещению</option>
              <option value="by_employee">По сотруднику</option>
              <option value="by_responsible">По ответственному лицу</option>
            </select>
          </div>

          {/* Scope */}
          {checkType !== 'full' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {checkType === 'by_room' ? 'Помещение' : checkType === 'by_employee' ? 'Сотрудник' : 'Ответственный'}
              </label>
              {loadingScope ? (
                <p className="text-sm text-gray-400">Загрузка...</p>
              ) : (
                <select
                  value={scopeId || ''}
                  onChange={(e) => setScopeId(Number(e.target.value) || null)}
                  className="w-full px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">— Выберите —</option>
                  {scopeOptions.map(opt => {
                    const isUser = (opt as any).type === 'user';
                    const isEmployee = (opt as any).type === 'employee';
                    const role = (opt as any).role;
                    return (
                      <option key={opt.id} value={opt.id}>
                        {opt.name}
                        {isUser ? (role === 'admin' ? ' 👑 (админ)' : ' 👤 (пользователь)') : ''}
                        {isEmployee && opt.position ? ` — ${opt.position}` : ''}
                        {opt.building ? ` (${opt.building})` : ''}
                        {opt.floor ? `, этаж ${opt.floor}` : ''}
                      </option>
                    );
                  })}
                </select>
              )}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2 mt-6">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 text-sm border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
          >
            Отмена
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="flex-1 px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
          >
            {submitting ? 'Создание...' : 'Создать'}
          </button>
        </div>
      </div>
    </div>
  );
};

// ====================== QR МОДАЛКА ======================

interface QrModalProps {
  check: InventoryCheck;
  onClose: () => void;
}

const QrModal: React.FC<QrModalProps> = ({ check, onClose }) => {
  const [qrText, setQrText] = useState('');
  const [qrUrl, setQrUrl] = useState('');
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetch(`/api/inventory-checks/${check.id}/qr-text`)
      .then(res => res.json())
      .then(data => {
        setQrText(data.qr_text || '');
        setQrUrl(data.qr_url || '');
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [check.id]);

  const handleCopy = () => {
    navigator.clipboard.writeText(qrUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success('Ссылка скопирована');
  };

  const handleDownloadQr = () => {
    const token = localStorage.getItem('token');
    const link = document.createElement('a');
    link.href = `/api/inventory-checks/${check.id}/qr-image${token ? `?token=${token}` : ''}`;
    link.download = `inventory_${check.id}_qr.png`;
    link.target = '_blank';
    link.click();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
          <QrCode className="w-5 h-5 text-blue-600" />
          QR-код инвентаризации
        </h3>

        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* QR preview */}
            <div className="flex justify-center">
              <div className="w-48 h-48 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-300 dark:border-gray-600">
                <img
                  src={`/api/inventory-checks/${check.id}/qr-image`}
                  alt="QR Code"
                  className="w-44 h-44 rounded"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                    (e.target as HTMLImageElement).nextElementSibling?.classList.remove('hidden');
                  }}
                />
                <div className="hidden text-center text-gray-400 text-xs p-4">
                  <QrCode className="w-8 h-8 mx-auto mb-1" />
                  QR-код недоступен
                </div>
              </div>
            </div>

            {/* Check info */}
            <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-sm">
              <p className="font-medium text-gray-900 dark:text-gray-100">{check.name}</p>
              <p className="text-xs text-gray-500 mt-0.5">
                {TYPE_LABELS[check.check_type]} • ID: {check.id}
              </p>
            </div>

            {/* URL */}
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Ссылка для проверки:</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  readOnly
                  value={qrUrl}
                  className="flex-1 px-3 py-2 text-xs border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                />
                <button
                  onClick={handleCopy}
                  className="px-3 py-2 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  {copied ? '✓' : 'Копировать'}
                </button>
              </div>
            </div>

            {/* QR text for external generation */}
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Текст для генерации QR:</label>
              <textarea
                readOnly
                value={qrText}
                rows={3}
                className="w-full px-3 py-2 text-xs font-mono border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <button
                onClick={handleDownloadQr}
                className="flex-1 inline-flex items-center justify-center gap-1.5 px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
              >
                <Download className="w-4 h-4" /> Скачать PNG
              </button>
              <button
                onClick={() => window.print()}
                className="flex-1 inline-flex items-center justify-center gap-1.5 px-4 py-2 text-sm border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
              >
                <Printer className="w-4 h-4" /> Печать
              </button>
            </div>
          </div>
        )}

        <button
          onClick={onClose}
          className="w-full mt-4 px-4 py-2 text-sm border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
        >
          Закрыть
        </button>
      </div>
    </div>
  );
};

export default Inventory;