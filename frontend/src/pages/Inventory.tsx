// frontend/src/pages/Inventory.tsx
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  ClipboardList, Plus, FileText, CheckCircle2, XCircle, Loader2,
  Building2, Users, User, Camera, ChevronRight, QrCode,
  ChevronLeft, Play, Trash2, Search, Clock, Check, X,
  RefreshCw, Package, Download, Printer, ArrowRight, AlertTriangle
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
  employee_id: number | null;
  employee_name: string | null;
  employee_position: string | null;
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
  const navigate = useNavigate();
  const { isAdmin, user } = useAuth();
  const [checks, setChecks] = useState<InventoryCheck[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCheck, setSelectedCheck] = useState<InventoryCheck | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showQrModal, setShowQrModal] = useState<InventoryCheck | null>(null);
  const [authErrorShown, setAuthErrorShown] = useState(false);

  const checkAuth = useCallback((): boolean => {
    const token = localStorage.getItem('token');
    if (!token) {
      if (!authErrorShown) {
        toast.error('Необходима авторизация. Войдите в систему.');
        setAuthErrorShown(true);
      }
      return false;
    }
    return true;
  }, [authErrorShown]);

  const clearAuth = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    toast.error('Сеанс истёк. Пожалуйста, войдите снова.');
    setTimeout(() => {
      window.location.href = '/login';
    }, 1500);
  }, []);

  const fetchChecks = useCallback(async () => {
    setLoading(true);
    setAuthErrorShown(false);
    try {
      if (!checkAuth()) {
        setLoading(false);
        return;
      }
      const token = localStorage.getItem('token')!;
      const res = await fetch('/api/inventory-checks', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setChecks(data);
      } else if (res.status === 401) {
        clearAuth();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Ошибка загрузки списка');
      }
    } catch (err) {
      console.error('fetchChecks error:', err);
      toast.error('Ошибка соединения с сервером');
    } finally {
      setLoading(false);
    }
  }, [checkAuth, clearAuth]);

  useEffect(() => {
    fetchChecks();
  }, [fetchChecks]);

  const fetchCheckDetails = async (checkId: number) => {
    const token = localStorage.getItem('token');
    if (!token) return;
    try {
      const res = await fetch(`/api/inventory-checks/${checkId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedCheck(data);
      } else if (res.status === 401) {
        clearAuth();
      }
    } catch (err) {
      console.error('fetchCheckDetails error:', err);
    }
  };

  const handleStart = async (checkId: number) => {
    if (!confirm('Начать инвентаризацию? Это сбросит статус проверки у всех активов.')) return;
    if (!checkAuth()) return;
    try {
      const token = localStorage.getItem('token')!;
      const res = await fetch(`/api/inventory-checks/${checkId}/start`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(data.message);
        fetchChecks();
        fetchCheckDetails(checkId);
      } else if (res.status === 401) {
        clearAuth();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Ошибка');
      }
    } catch (err) {
      console.error('handleStart error:', err);
      toast.error('Ошибка соединения');
    }
  };

  const handleComplete = async (checkId: number) => {
    if (!confirm('Завершить инвентаризацию?')) return;
    if (!checkAuth()) return;
    try {
      const token = localStorage.getItem('token')!;
      const res = await fetch(`/api/inventory-checks/${checkId}/complete`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(data.message);
        fetchChecks();
        fetchCheckDetails(checkId);
      } else if (res.status === 401) {
        clearAuth();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Ошибка');
      }
    } catch (err) {
      console.error('handleComplete error:', err);
      toast.error('Ошибка соединения');
    }
  };

  const handleDelete = async (checkId: number) => {
    if (!confirm('Удалить инвентаризацию? Это действие необратимо.')) return;
    if (!checkAuth()) return;
    try {
      const token = localStorage.getItem('token')!;
      const res = await fetch(`/api/inventory-checks/${checkId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        toast.success('Инвентаризация удалена');
        setSelectedCheck(null);
        fetchChecks();
      } else if (res.status === 401) {
        clearAuth();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Ошибка');
      }
    } catch (err) {
      console.error('handleDelete error:', err);
      toast.error('Ошибка соединения');
    }
  };

  const handleConfirm = async (checkId: number, assetId: number, found: boolean) => {
    if (!checkAuth()) return;
    try {
      const token = localStorage.getItem('token')!;
      const res = await fetch(
        `/api/inventory-checks/${checkId}/confirm/${assetId}?found=${found}`,
        { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } }
      );
      if (res.ok) {
        toast.success(found ? 'Актив найден' : 'Актив отмечен как отсутствующий');
        fetchCheckDetails(checkId);
      } else if (res.status === 401) {
        clearAuth();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Ошибка');
      }
    } catch (err) {
      console.error('handleConfirm error:', err);
      toast.error('Ошибка соединения');
    }
  };

  const handleSkip = async (checkId: number, assetId: number) => {
    if (!checkAuth()) return;
    try {
      const token = localStorage.getItem('token')!;
      const res = await fetch(
        `/api/inventory-checks/${checkId}/confirm/${assetId}?skip=true`,
        { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } }
      );
      if (res.ok) {
        toast.success('Актив пропущен');
        fetchCheckDetails(checkId);
      } else if (res.status === 401) {
        clearAuth();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Ошибка пропуска');
      }
    } catch (err) {
      console.error('handleSkip error:', err);
      toast.error('Ошибка соединения');
    }
  };

  const handleResetAsset = async (checkId: number, assetId: number) => {
    if (!checkAuth()) return;
    try {
      const token = localStorage.getItem('token')!;
      const res = await fetch(
        `/api/inventory-checks/${checkId}/reset-asset/${assetId}`,
        { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } }
      );
      if (res.ok) {
        toast.success('Статус сброшен');
        fetchCheckDetails(checkId);
      } else if (res.status === 401) {
        clearAuth();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Ошибка');
      }
    } catch (err) {
      console.error('handleResetAsset error:', err);
      toast.error('Ошибка соединения');
    }
  };

  const handleMarkAllFound = async (checkId: number) => {
    if (!checkAuth()) return;
    if (!confirm('Подтвердить все найденные активы? Это действие отметит все ожидающие активы как найденные.')) return;
    try {
      const token = localStorage.getItem('token')!;
      const res = await fetch(
        `/api/inventory-checks/${checkId}/mark-all-found`,
        { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        toast.success(`Все активы отмечены как найденные (${data.marked} шт.)`);
        fetchCheckDetails(checkId);
      } else if (res.status === 401) {
        clearAuth();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Ошибка');
      }
    } catch (err) {
      console.error('handleMarkAllFound error:', err);
      toast.error('Ошибка соединения');
    }
  };

  // ====================== РЕНДЕР ======================

  if (loading) {
    return (
      <div className="flex justify-center items-center py-16">
        <div className="text-center">
          <Loader2 className="w-10 h-10 animate-spin mx-auto mb-3 text-brand-500 dark:text-accent-400" />
          <p className="text-gray-500 dark:text-gray-400 text-sm">Загрузка...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <ClipboardList className="w-6 h-6 text-brand-600 dark:text-accent-400" />
            Инвентаризация
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            Сверка имущества по помещениям, сотрудникам и ответственным лицам
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => navigate('/inventory-mobile')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-accent-400 text-graphite-900 text-xs rounded-card-sm hover:bg-accent-500 transition font-medium"
          >
            <Camera className="w-3.5 h-3.5" />
            Мобильная
          </button>
          {isAdmin && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-brand-500 text-white text-xs rounded-card-sm hover:bg-brand-600 transition font-medium"
            >
              <Plus className="w-3.5 h-3.5" />
              Создать
            </button>
          )}
        </div>
      </div>

      {/* List view */}
      {!selectedCheck && (
        <>
          {checks.length === 0 ? (
            <div className="card-modern p-8 text-center">
              <ClipboardList className="w-12 h-12 text-brand-300 dark:text-brand-600 mx-auto mb-3" />
              <h3 className="text-base font-semibold text-gray-700 dark:text-gray-300 mb-1">Нет инвентаризаций</h3>
              <p className="text-gray-500 dark:text-gray-400 text-sm">
                {isAdmin
                  ? 'Создайте первую инвентаризацию для сверки имущества'
                  : 'Инвентаризации пока не созданы'}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {checks.map((check) => {
                const statusColor = {
                  draft: 'badge-inactive',
                  in_progress: 'badge-active',
                  completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
                  cancelled: 'badge-inactive',
                }[check.status] || 'badge-inactive';

                const statusText = {
                  draft: 'Черновик',
                  in_progress: 'В процессе',
                  completed: 'Завершена',
                  cancelled: 'Отменена',
                }[check.status];

                return (
                  <div
                    key={check.id}
                    className="card-modern p-4 cursor-pointer group"
                    onClick={() => fetchCheckDetails(check.id)}
                  >
                    <div className="flex items-start justify-between mb-2.5">
                      <div className="flex items-center gap-2.5">
                        <div className="w-9 h-9 rounded-card-sm bg-brand-50 dark:bg-brand-900/20 flex items-center justify-center text-brand-600 dark:text-accent-400 group-hover:bg-brand-100 dark:group-hover:bg-brand-900/30 transition-colors">
                          {TYPE_ICONS[check.check_type]}
                        </div>
                        <div>
                          <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">{check.name}</h3>
                          <p className="text-[11px] text-gray-500 dark:text-gray-400">
                            {TYPE_LABELS[check.check_type]}
                            {check.scope_name ? ` • ${check.scope_name}` : ''}
                          </p>
                        </div>
                      </div>
                      <span className={statusColor}>{statusText}</span>
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-center mb-2.5">
                      <div className="bg-gray-50 dark:bg-graphite-800/50 rounded-card-sm p-1.5">
                        <p className="text-base font-bold text-gray-900 dark:text-gray-100">{check.total_checked}</p>
                        <p className="text-[10px] text-gray-500 dark:text-gray-400">Всего</p>
                      </div>
                      <div className="bg-green-50 dark:bg-green-900/10 rounded-card-sm p-1.5">
                        <p className="text-base font-bold text-green-600 dark:text-green-400">{check.found}</p>
                        <p className="text-[10px] text-gray-500 dark:text-gray-400">Найдено</p>
                      </div>
                      <div className="bg-red-50 dark:bg-red-900/10 rounded-card-sm p-1.5">
                        <p className="text-base font-bold text-red-600 dark:text-red-400">{check.missing}</p>
                        <p className="text-[10px] text-gray-500 dark:text-gray-400">Нет</p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-gray-400 dark:text-gray-500 mb-2">
                      <span>{check.creator_name || '—'}</span>
                      <span>{check.created_at ? new Date(check.created_at).toLocaleDateString('ru-RU') : '—'}</span>
                    </div>

                    <button
                      onClick={(e) => { e.stopPropagation(); fetchCheckDetails(check.id); }}
                      className="w-full px-3 py-1.5 text-xs bg-brand-500 dark:bg-brand-600 text-white rounded-card-sm hover:bg-brand-600 dark:hover:bg-brand-700 transition flex items-center justify-center gap-1 font-medium"
                    >
                      <ChevronRight className="w-3.5 h-3.5" /> Открыть
                    </button>
                  </div>
                );
              })}
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
          onSkip={handleSkip}
          onResetAsset={handleResetAsset}
          onMarkAllFound={handleMarkAllFound}
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
  onSkip: (checkId: number, assetId: number) => void;
  onResetAsset: (checkId: number, assetId: number) => void;
  onMarkAllFound: (checkId: number) => void;
  onRefresh: () => void;
  onShowQr: () => void;
}

const CheckDetailView: React.FC<CheckDetailViewProps> = ({
  check, isAdmin, onBack, onStart, onComplete, onDelete, onConfirm, onSkip, onResetAsset, onMarkAllFound, onRefresh, onShowQr
}) => {
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'pending' | 'found' | 'missing'>('all');
  const [autoRefresh, setAutoRefresh] = useState(true);

  const items = check.items || [];
  const filtered = items.filter(item => {
    if (filter !== 'all' && item.result !== filter) return false;
    if (search) {
      const s = search.toLowerCase();
      return (item.inventory_number || '').toLowerCase().includes(s) ||
             (item.asset_name || '').toLowerCase().includes(s) ||
             (item.location || '').toLowerCase().includes(s);
    }
    return true;
  });

  const pendingCount = items.filter(i => i.result === 'pending').length;
  const foundCount = items.filter(i => i.result === 'found').length;
  const missingCount = items.filter(i => i.result === 'missing').length;
  const progress = items.length > 0 ? ((foundCount + missingCount) / items.length * 100).toFixed(0) : '0';

  // Автообновление при сканировании RFID
  useEffect(() => {
    if (check.status !== 'in_progress' || !autoRefresh) return;
    
    const interval = setInterval(() => {
      onRefresh();
    }, 5000); // Обновление каждые 5 секунд
    
    return () => clearInterval(interval);
  }, [check.status, autoRefresh, onRefresh]);

  return (
    <div className="space-y-4">
      {/* Top bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 hover:text-brand-600 dark:hover:text-accent-400 transition"
        >
          <ChevronLeft className="w-3.5 h-3.5" /> Назад к списку
        </button>

        <div className="flex gap-2 flex-wrap">
          {isAdmin && check.status === 'draft' && (
            <button
              onClick={() => onStart(check.id)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-accent-400 text-graphite-900 text-xs rounded-card-sm hover:bg-accent-500 transition font-medium"
            >
              <Play className="w-3.5 h-3.5" /> Начать
            </button>
          )}
          {isAdmin && check.status === 'in_progress' && (
            <>
              <button
                onClick={onShowQr}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-gray-200 dark:border-graphite-700 text-gray-600 dark:text-gray-400 text-xs rounded-card-sm hover:bg-gray-50 dark:hover:bg-graphite-800 transition"
              >
                <QrCode className="w-3.5 h-3.5" /> QR-код
              </button>
              <button
                onClick={() => onComplete(check.id)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-brand-500 text-white text-xs rounded-card-sm hover:bg-brand-600 transition font-medium"
              >
                <CheckCircle2 className="w-3.5 h-3.5" /> Завершить
              </button>
            </>
          )}
          {isAdmin && (check.status === 'draft' || check.status === 'cancelled') && (
            <button
              onClick={() => onDelete(check.id)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-50 text-red-600 dark:bg-red-900/20 dark:text-red-400 text-xs rounded-card-sm hover:bg-red-100 dark:hover:bg-red-900/40 transition"
            >
              <Trash2 className="w-3.5 h-3.5" /> Удалить
            </button>
          )}
        </div>
      </div>

      {/* Info card */}
      <div className="card-modern p-4">
        <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
          <div>
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              {TYPE_ICONS[check.check_type]}
              {check.name}
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              {TYPE_LABELS[check.check_type]}
              {check.scope_name ? ` • ${check.scope_name}` : ''}
              {check.department_name ? ` • ${check.department_name}` : ''}
            </p>
          </div>
          <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
            check.status === 'draft' ? 'badge-inactive' :
            check.status === 'in_progress' ? 'badge-active' :
            check.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
            'badge-inactive'
          }`}>
            {STATUS_LABELS[check.status]}
          </span>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
          <div className="bg-gray-50 dark:bg-graphite-800/50 rounded-card-sm p-2.5 text-center">
            <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{check.total_checked}</p>
            <p className="text-[10px] text-gray-500 dark:text-gray-400">Всего активов</p>
          </div>
          <div className="bg-green-50 dark:bg-green-900/10 rounded-card-sm p-2.5 text-center">
            <p className="text-xl font-bold text-green-600 dark:text-green-400">{foundCount}</p>
            <p className="text-[10px] text-gray-500 dark:text-gray-400">Найдено</p>
          </div>
          <div className="bg-red-50 dark:bg-red-900/10 rounded-card-sm p-2.5 text-center">
            <p className="text-xl font-bold text-red-600 dark:text-red-400">{missingCount}</p>
            <p className="text-[10px] text-gray-500 dark:text-gray-400">Отсутствует</p>
          </div>
          <div className="bg-yellow-50 dark:bg-yellow-900/10 rounded-card-sm p-2.5 text-center">
            <p className="text-xl font-bold text-yellow-600 dark:text-yellow-400">{pendingCount}</p>
            <p className="text-[10px] text-gray-500 dark:text-gray-400">Осталось</p>
          </div>
        </div>

        {/* Progress bar */}
        {check.status === 'in_progress' && (
          <div className="mb-3">
            <div className="flex justify-between items-center text-[10px] text-gray-500 dark:text-gray-400 mb-1">
              <span>Прогресс проверки</span>
              <div className="flex items-center gap-2">
                <span className="font-medium">{progress}%</span>
                {autoRefresh && (
                  <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
                    <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                    Авто
                  </span>
                )}
              </div>
            </div>
            <div className="progress-bar-modern">
              <div
                className="progress-bar-fill bg-accent-400"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Meta info */}
        <div className="flex flex-wrap gap-3 text-[10px] text-gray-400 dark:text-gray-500">
          <span>Создал: {check.creator_name || '—'}</span>
          <span>Дата: {check.check_date ? new Date(check.check_date).toLocaleDateString('ru-RU') : '—'}</span>
          {check.started_at && <span>Начата: {new Date(check.started_at).toLocaleString('ru-RU')}</span>}
          {check.completed_at && <span>Завершена: {new Date(check.completed_at).toLocaleString('ru-RU')}</span>}
        </div>
      </div>

      {/* Items */}
      {check.status === 'in_progress' || check.status === 'completed' ? (
        <div className="card-modern p-4">
          {/* Auto-scan notice */}
          {check.status === 'in_progress' && (
            <div className="mb-3 p-2.5 bg-accent-50 dark:bg-accent-900/10 border border-accent-200 dark:border-accent-800/50 rounded-card-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="rfid-scan-indicator w-4 h-4">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-accent-500"></span>
                    </span>
                  </span>
                  <p className="text-xs text-accent-800 dark:text-accent-300">
                    RFID-метки сканируются автоматически
                  </p>
                </div>
                <button
                  onClick={() => setAutoRefresh(!autoRefresh)}
                  className={`px-2 py-0.5 text-[10px] rounded transition ${
                    autoRefresh
                      ? 'bg-accent-400 text-graphite-900 font-medium'
                      : 'bg-gray-200 dark:bg-graphite-800 text-gray-600 dark:text-gray-400'
                  }`}
                >
                  {autoRefresh ? 'Вкл' : 'Выкл'}
                </button>
              </div>
            </div>
          )}

          {/* Filters with search */}
          <div className="flex flex-wrap gap-2 mb-3">
            <div className="flex-1 min-w-[180px] relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Поиск по инв. номеру..."
                className="search-input-modern"
              />
            </div>
            <div className="flex gap-1">
              {(['all', 'pending', 'found', 'missing'] as const).map(f => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-2.5 py-1 text-[11px] rounded-card-sm transition ${
                    filter === f
                      ? 'bg-brand-500 text-white font-medium'
                      : 'bg-gray-100 dark:bg-graphite-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-graphite-700'
                  }`}
                >
                  {f === 'all' ? 'Все' : f === 'pending' ? 'Ожидают' : f === 'found' ? 'Найдены' : 'Нет'}
                </button>
              ))}
            </div>
            {pendingCount > 0 && check.status === 'in_progress' && (
              <button
                onClick={() => onMarkAllFound(check.id)}
                className="px-2.5 py-1 text-[11px] bg-green-600 text-white rounded-card-sm hover:bg-green-700 transition flex items-center gap-1 font-medium"
              >
                <CheckCircle2 className="w-3 h-3" />
                Подтвердить все ({pendingCount})
              </button>
            )}
          </div>

          {/* Items list */}
          {filtered.length === 0 ? (
            <p className="text-center text-gray-400 py-6 text-sm">Нет активов для отображения</p>
          ) : (
            <div className="space-y-1.5 max-h-[450px] overflow-y-auto pr-1">
              {filtered.map(item => (
                <div
                  key={item.id}
                  className={`flex items-center gap-2.5 p-2.5 rounded-card-sm border transition-all duration-200 ${
                    item.result === 'found'
                      ? 'border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-900/10'
                      : item.result === 'missing'
                      ? 'border-red-200 dark:border-red-800 bg-red-50/50 dark:bg-red-900/10'
                      : 'border-gray-100 dark:border-graphite-800 hover:border-brand-200 dark:hover:border-brand-800'
                  }`}
                >
                  {/* Status indicator */}
                  <div className="flex-shrink-0">
                    {item.result === 'found' ? (
                      <div className="w-6 h-6 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                        <CheckCircle2 className="w-4 h-4 text-green-600 dark:text-green-400" />
                      </div>
                    ) : item.result === 'missing' ? (
                      <div className="w-6 h-6 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                        <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400" />
                      </div>
                    ) : (
                      <div className="w-6 h-6 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
                        <Clock className="w-4 h-4 text-yellow-600 dark:text-yellow-400" />
                      </div>
                    )}
                  </div>

                  {/* Asset info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono text-[10px] text-gray-500 dark:text-gray-400">{item.inventory_number}</span>
                      <span className="font-medium text-sm text-gray-900 dark:text-gray-100 truncate">{item.asset_name}</span>
                      <span className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium ${
                        item.result === 'found'
                          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                          : item.result === 'missing'
                          ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                          : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                      }`}>
                        {item.result === 'found' ? 'Найден' : item.result === 'missing' ? 'Нет' : '—'}
                      </span>
                    </div>
                    <div className="text-[10px] text-gray-400 dark:text-gray-500 flex flex-wrap gap-1.5 mt-0.5">
                      {item.model && <span>{item.model}</span>}
                      {item.location && <span>📍 {item.location}</span>}
                      {item.responsible && <span>👤 {item.responsible}</span>}
                      {item.confirmed_by && <span className="text-green-600 dark:text-green-400">✓ {item.confirmed_by}</span>}
                    </div>
                  </div>

                  {/* Action buttons */}
                  <div className="flex-shrink-0 flex gap-1 flex-wrap justify-end">
                    {check.status === 'in_progress' && (
                      <>
                        {item.result === 'pending' && (
                          <>
                            <button
                              onClick={() => onConfirm(check.id, item.asset_id, true)}
                              className="px-2 py-0.5 text-[10px] bg-green-600 text-white rounded hover:bg-green-700 transition flex items-center gap-0.5"
                              title="Найден"
                            >
                              <Check className="w-3 h-3" /> Да
                            </button>
                            <button
                              onClick={() => onConfirm(check.id, item.asset_id, false)}
                              className="px-2 py-0.5 text-[10px] bg-red-600 text-white rounded hover:bg-red-700 transition flex items-center gap-0.5"
                              title="Отсутствует"
                            >
                              <X className="w-3 h-3" /> Нет
                            </button>
                            <button
                              onClick={() => onSkip(check.id, item.asset_id)}
                              className="px-2 py-0.5 text-[10px] border border-gray-300 dark:border-graphite-700 text-gray-500 dark:text-gray-400 rounded hover:bg-gray-50 dark:hover:bg-graphite-800 transition"
                              title="Пропустить"
                            >
                              ⏭
                            </button>
                          </>
                        )}
                        {item.result !== 'pending' && (
                          <span className="px-1.5 py-0.5 text-[10px] text-gray-500 dark:text-gray-400">
                            {item.result === 'found' ? '✓' : '✗'}
                          </span>
                        )}
                        {isAdmin && item.result !== 'pending' && (
                          <button
                            onClick={() => onResetAsset(check.id, item.asset_id)}
                            className="px-1.5 py-0.5 text-[10px] border border-gray-200 dark:border-graphite-700 text-gray-400 rounded hover:bg-gray-50 dark:hover:bg-graphite-800 transition"
                            title="Сбросить"
                          >
                            <RefreshCw className="w-3 h-3" />
                          </button>
                        )}
                      </>
                    )}
                    {check.status === 'completed' && isAdmin && (
                      <button
                        onClick={() => onResetAsset(check.id, item.asset_id)}
                        className="px-1.5 py-0.5 text-[10px] border border-gray-200 dark:border-graphite-700 text-gray-400 rounded hover:bg-gray-50 dark:hover:bg-graphite-800 transition"
                        title="Сбросить"
                      >
                        <RefreshCw className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="card-modern p-6 text-center">
          <FileText className="w-8 h-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            {check.status === 'draft'
              ? 'Инвентаризация не начата. Нажмите "Начать" для запуска.'
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
  const [scopeError, setScopeError] = useState<string | null>(null);
  const [selectedEmployeeInfo, setSelectedEmployeeInfo] = useState<{
    position?: string;
    room?: string;
  } | null>(null);

  useEffect(() => {
    if (checkType !== 'full') {
      loadScopeOptions();
    } else {
      setScopeOptions([]);
      setScopeId(null);
      setScopeError(null);
    }
  }, [checkType]);

  const loadScopeOptions = async () => {
    setLoadingScope(true);
    setScopeError(null);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setScopeError('Необходима авторизация');
        setScopeOptions([]);
        setLoadingScope(false);
        return;
      }
      const res = await fetch(`/api/inventory-checks/scope-options?check_type=${checkType}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setScopeOptions(Array.isArray(data) ? data : []);
      } else if (res.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      } else {
        const err = await res.json().catch(() => ({}));
        setScopeError(err.detail || `Ошибка ${res.status}`);
        setScopeOptions([]);
      }
    } catch (err) {
      console.error('loadScopeOptions error:', err);
      setScopeError('Ошибка соединения');
      setScopeOptions([]);
    } finally {
      setLoadingScope(false);
    }
  };

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
      // Добавляем сотрудника-подписанта
      if (selectedEmployeeInfo && scopeId) {
        const opt = scopeOptions.find(o => o.id === scopeId);
        if (opt && (opt as any).type === 'employee') {
          params.append('employee_id', String(scopeId));
          params.append('employee_name', opt.name);
          params.append('employee_position', selectedEmployeeInfo.position || '');
        }
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
                {checkType === 'by_room' ? 'Помещение' : checkType === 'by_employee' ? 'Сотрудник (подписант)' : 'Ответственный'}
              </label>
              {loadingScope ? (
                <p className="text-sm text-gray-400">Загрузка...</p>
              ) : scopeError ? (
                <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <p className="text-sm text-red-600 dark:text-red-400">{scopeError}</p>
                  <button
                    onClick={loadScopeOptions}
                    className="mt-2 text-xs text-red-700 dark:text-red-300 underline hover:no-underline"
                  >
                    Повторить
                  </button>
                </div>
              ) : scopeOptions.length === 0 ? (
                <p className="text-sm text-gray-400">Нет доступных объектов для выбора</p>
              ) : (
                <>
                  <select
                    value={scopeId || ''}
                    onChange={(e) => {
                      const val = Number(e.target.value) || null;
                      setScopeId(val);
                      // Получаем информацию о выбранном сотруднике
                      if (val) {
                        const opt = scopeOptions.find(o => o.id === val);
                        if (opt && (opt as any).type === 'employee') {
                          setSelectedEmployeeInfo({
                            position: (opt as any).position,
                            room: (opt as any).room,
                          });
                        } else {
                          setSelectedEmployeeInfo(null);
                        }
                      } else {
                        setSelectedEmployeeInfo(null);
                      }
                    }}
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
                  {/* Отображение информации о выбранном сотруднике */}
                  {selectedEmployeeInfo && scopeId && (
                    <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                      <p className="text-xs font-medium text-blue-800 dark:text-blue-200 mb-1">Информация о подписанте:</p>
                      <div className="text-xs text-blue-700 dark:text-blue-300 space-y-0.5">
                        {selectedEmployeeInfo.position && (
                          <p>Должность: {selectedEmployeeInfo.position}</p>
                        )}
                        {selectedEmployeeInfo.room && (
                          <p>Кабинет: {selectedEmployeeInfo.room}</p>
                        )}
                      </div>
                    </div>
                  )}
                </>
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