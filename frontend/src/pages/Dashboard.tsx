// frontend/src/pages/Dashboard.tsx
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  ClipboardCheck, CheckCircle2, Clock, Loader2, Wrench, TrendingUp,
  Package, Building2, AlertTriangle, ArrowRight,
  FileCheck, Hammer, DollarSign, Eye, Database,
} from 'lucide-react';

interface Stats {
  total: number;
  active: number;
  maintenance: number;
  written_off: number;
  rooms: number;
  errors: number;
}

interface TopAssetType {
  type: string;
  count: number;
}

interface RepairStats {
  total_repairs: number;
  pending: number;
  in_progress: number;
  completed: number;
  rejected: number;
  cancelled: number;
  active_repair_assets: number;
  total_estimated_cost: number;
  total_actual_cost: number;
  top_asset_types: TopAssetType[];
}

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
}

interface InventoryCheck {
  id: number;
  name: string;
  check_type: string;
  started_at: string;
  found: number;
  missing: number;
  total_checked: number;
  items?: InventoryCheckItem[];
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<Stats>({
    total: 0, active: 0, maintenance: 0, written_off: 0, rooms: 0, errors: 0,
  });
  const [activeInventory, setActiveInventory] = useState<InventoryCheck | null>(null);
  const [inventoryLoading, setInventoryLoading] = useState(false);
  const [repairStats, setRepairStats] = useState<RepairStats | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      
      const statsResponse = await fetch('/api/reports/inventory-report', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        if (statsData.summary) {
          setStats({
            total: statsData.summary.total_count || 0,
            active: (statsData.status_breakdown?.find((s: any) => s.status === 'active')?.count) || 0,
            maintenance: statsData.summary.needs_repair_count || 0,
            written_off: (statsData.status_breakdown?.find((s: any) => s.status === 'written_off')?.count) || 0,
            rooms: statsData.rooms_count || 0,
            errors: statsData.errors_count || 0,
          });
        }
      }

      setInventoryLoading(true);
      const invResponse = await fetch('/api/inventory-checks/active', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
      });
      if (invResponse.ok) {
        const invData = await invResponse.json();
        setActiveInventory(invData);
      }
      setInventoryLoading(false);

      try {
        const repairResponse = await fetch('/api/repairs/stats/', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
        });
        if (repairResponse.ok) {
          const repairData = await repairResponse.json();
          setRepairStats(repairData);
        }
      } catch {
        // Repair stats not available
      }
    } catch {
      // Silent fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-graphite-950">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Загрузка...</h2>
        </div>
      </div>
    );
  }

  const summaryWidgets = [
    {
      label: 'Всего активов',
      value: stats.total,
      icon: <Package className="w-5 h-5" />,
      color: 'text-brand-600 dark:text-brand-400',
      bg: 'bg-brand-50 dark:bg-brand-900/20',
      sub: `${stats.active} активных`,
    },
    {
      label: 'Помещений',
      value: stats.rooms || '—',
      icon: <Building2 className="w-5 h-5" />,
      color: 'text-accent-600 dark:text-accent-400',
      bg: 'bg-accent-50 dark:bg-accent-900/20',
      sub: 'Площадки',
    },
    {
      label: 'На ремонте',
      value: stats.maintenance,
      icon: <Hammer className="w-5 h-5" />,
      color: 'text-yellow-600 dark:text-yellow-400',
      bg: 'bg-yellow-50 dark:bg-yellow-900/20',
      sub: 'Требуют внимания',
    },
    {
      label: 'Ошибки',
      value: stats.errors,
      icon: <AlertTriangle className="w-5 h-5" />,
      color: stats.errors > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-400 dark:text-gray-500',
      bg: stats.errors > 0 ? 'bg-red-50 dark:bg-red-900/20' : 'bg-gray-50 dark:bg-gray-800/50',
      sub: stats.errors > 0 ? 'Требуют проверки' : 'Всё в порядке',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-graphite-950">
      {loading ? (
        <div className="flex justify-center items-center py-24">
          <div className="text-center">
            <Loader2 className="w-10 h-10 animate-spin mx-auto mb-3 text-brand-500 dark:text-accent-400" />
            <p className="text-gray-500 dark:text-gray-400 text-sm">Загрузка данных...</p>
          </div>
        </div>
      ) : (
        <main className="px-4 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Дашборд</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">Обзор системы управления активами</p>
          </div>

          {/* Summary widgets */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
            {summaryWidgets.map((w) => (
              <div key={w.label} className="widget-summary">
                <div className={`p-2.5 rounded-card-sm ${w.bg}`}>
                  <span className={w.color}>{w.icon}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-lg font-bold text-gray-900 dark:text-gray-100 truncate">{w.value}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{w.label}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Active inventory card */}
          {inventoryLoading ? (
            <div className="card-modern p-5 mb-6">
              <div className="flex items-center justify-center py-6">
                <Loader2 className="w-6 h-6 animate-spin text-brand-500 dark:text-accent-400" />
                <span className="ml-2 text-gray-500 dark:text-gray-400 text-sm">Загрузка...</span>
              </div>
            </div>
          ) : activeInventory ? (
            <div className="card-modern p-5 mb-6 border-l-4 border-l-accent-400">
              <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-card-sm bg-accent-100 dark:bg-accent-900/30">
                    <ClipboardCheck className="w-5 h-5 text-accent-600 dark:text-accent-400" />
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-900 dark:text-gray-100">{activeInventory.name}</h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {activeInventory.check_type === 'full' ? 'Полная' :
                       activeInventory.check_type === 'by_room' ? 'По помещениям' :
                       activeInventory.check_type === 'by_employee' ? 'По сотрудникам' : 'По ответственному'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 px-2.5 py-1 bg-accent-100 dark:bg-accent-900/30 rounded-full">
                  <span className="w-2 h-2 bg-accent-500 rounded-full animate-pulse"></span>
                  <span className="text-xs font-medium text-accent-700 dark:text-accent-400">В процессе</span>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <div className="bg-gray-50 dark:bg-graphite-800/50 rounded-card-sm p-2.5 text-center">
                  <div className="flex items-center justify-center gap-1 mb-0.5">
                    <Clock className="w-3.5 h-3.5 text-gray-400" />
                    <span className="text-[10px] text-gray-500 dark:text-gray-400">Начата</span>
                  </div>
                  <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {activeInventory.started_at ? new Date(activeInventory.started_at).toLocaleDateString('ru-RU') : '—'}
                  </p>
                </div>
                <div className="bg-gray-50 dark:bg-graphite-800/50 rounded-card-sm p-2.5 text-center">
                  <div className="flex items-center justify-center gap-1 mb-0.5">
                    <Package className="w-3.5 h-3.5 text-gray-400" />
                    <span className="text-[10px] text-gray-500 dark:text-gray-400">Всего</span>
                  </div>
                  <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{activeInventory.total_checked}</p>
                </div>
                <div className="bg-green-50 dark:bg-green-900/10 rounded-card-sm p-2.5 text-center">
                  <div className="flex items-center justify-center gap-1 mb-0.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                    <span className="text-[10px] text-gray-500 dark:text-gray-400">Найдено</span>
                  </div>
                  <p className="text-lg font-bold text-green-600 dark:text-green-400">{activeInventory.found}</p>
                </div>
                <div className="bg-red-50 dark:bg-red-900/10 rounded-card-sm p-2.5 text-center">
                  <div className="flex items-center justify-center gap-1 mb-0.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-red-500" />
                    <span className="text-[10px] text-gray-500 dark:text-gray-400">Отсутствует</span>
                  </div>
                  <p className="text-lg font-bold text-red-600 dark:text-red-400">{activeInventory.missing}</p>
                </div>
              </div>

              {/* Progress */}
              <div className="mb-4">
                <div className="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400 mb-1">
                  <span>Прогресс</span>
                  <span className="font-medium">
                    {activeInventory.total_checked > 0 
                      ? Math.round(((activeInventory.found + activeInventory.missing) / activeInventory.total_checked) * 100) 
                      : 0}%
                  </span>
                </div>
                <div className="progress-bar-modern">
                  <div
                    className="progress-bar-fill bg-accent-400"
                    style={{
                      width: `${activeInventory.total_checked > 0 
                        ? ((activeInventory.found + activeInventory.missing) / activeInventory.total_checked) * 100 
                        : 0}%`,
                    }}
                  />
                </div>
              </div>

              {/* Recent items */}
              {activeInventory.items && activeInventory.items.length > 0 && (
                <div className="mb-4">
                  <div className="max-h-40 overflow-y-auto space-y-1.5 pr-1">
                    {activeInventory.items.slice(0, 8).map((item) => (
                      <div
                        key={item.id}
                        className={`flex items-center gap-2 px-3 py-2 rounded-card-sm border text-xs transition ${
                          item.result === 'found'
                            ? 'border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-900/10'
                            : item.result === 'missing'
                            ? 'border-red-200 dark:border-red-800 bg-red-50/50 dark:bg-red-900/10'
                            : 'border-gray-100 dark:border-graphite-800'
                        }`}
                      >
                        {item.result === 'found' ? (
                          <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                        ) : item.result === 'missing' ? (
                          <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
                        ) : (
                          <Clock className="w-4 h-4 text-gray-400 flex-shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                          <span className="font-mono text-gray-500 dark:text-gray-400">{item.inventory_number}</span>
                          <span className="ml-1.5 font-medium text-gray-800 dark:text-gray-200 truncate">{item.asset_name}</span>
                        </div>
                        {item.location && <span className="text-gray-400 text-[10px]">📍 {item.location}</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => navigate('/inventory')}
                  className="btn-accent-modern flex-1 text-sm"
                >
                  <Eye className="w-4 h-4" />
                  Перейти к инвентаризации
                  <ArrowRight className="w-4 h-4" />
                </button>
                <button
                  onClick={() => navigate('/assets')}
                  className="btn-ghost-modern flex-1 text-sm"
                >
                  Смотреть активы
                </button>
              </div>
            </div>
          ) : (
            <div className="card-modern p-5 mb-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-card-sm bg-gray-100 dark:bg-graphite-800">
                    <ClipboardCheck className="w-5 h-5 text-gray-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-800 dark:text-gray-100">Нет активных инвентаризаций</h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Создайте новую проверку</p>
                  </div>
                </div>
                <button
                  onClick={() => navigate('/inventory')}
                  className="btn-primary-modern text-sm"
                >
                  <FileCheck className="w-4 h-4" />
                  Создать
                </button>
              </div>
            </div>
          )}

          {/* Repairs + Top asset types */}
          {repairStats && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
              {/* Repair stats */}
              <div className="card-modern p-5">
                <h3 className="font-semibold text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2">
                  <Wrench className="w-4 h-4 text-brand-500 dark:text-accent-400" />
                  Заявки на ремонт
                </h3>
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div className="bg-brand-50 dark:bg-brand-900/20 rounded-card-sm p-3">
                    <div className="text-xl font-bold text-brand-600 dark:text-brand-400">{repairStats.total_repairs}</div>
                    <div className="text-[11px] text-gray-500 dark:text-gray-400">Всего заявок</div>
                  </div>
                  <div className="bg-accent-50 dark:bg-accent-900/20 rounded-card-sm p-3">
                    <div className="text-xl font-bold text-accent-600 dark:text-accent-400">{repairStats.in_progress}</div>
                    <div className="text-[11px] text-gray-500 dark:text-gray-400">В работе</div>
                  </div>
                  <div className="bg-green-50 dark:bg-green-900/20 rounded-card-sm p-3">
                    <div className="text-xl font-bold text-green-600 dark:text-green-400">{repairStats.completed}</div>
                    <div className="text-[11px] text-gray-500 dark:text-gray-400">Завершено</div>
                  </div>
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-card-sm p-3">
                    <div className="text-xl font-bold text-yellow-600 dark:text-yellow-400">{repairStats.active_repair_assets}</div>
                    <div className="text-[11px] text-gray-500 dark:text-gray-400">В ремонте</div>
                  </div>
                </div>
                <div className="flex justify-between items-center text-xs pt-2 border-t border-gray-100 dark:border-graphite-800">
                  <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                    <DollarSign className="w-3 h-3" /> Смета
                  </span>
                  <span className="font-semibold text-gray-800 dark:text-gray-200">{repairStats.total_estimated_cost.toLocaleString('ru-RU')} ₽</span>
                </div>
                <div className="flex justify-between items-center text-xs mt-1">
                  <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                    <DollarSign className="w-3 h-3" /> Факт
                  </span>
                  <span className="font-semibold text-gray-800 dark:text-gray-200">{repairStats.total_actual_cost.toLocaleString('ru-RU')} ₽</span>
                </div>
              </div>

              {/* Top asset types */}
              {repairStats.top_asset_types.length > 0 && (
                <div className="card-modern p-5">
                  <h3 className="font-semibold text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-brand-500 dark:text-accent-400" />
                    Топ-5 типов по ремонтам
                  </h3>
                  <div className="space-y-2.5">
                    {repairStats.top_asset_types.map((item, idx) => {
                      const maxCount = repairStats.top_asset_types[0]?.count || 1;
                      const pct = Math.round((item.count / maxCount) * 100);
                      const barColors = [
                        'bg-brand-500 dark:bg-brand-400',
                        'bg-brand-400 dark:bg-brand-300',
                        'bg-accent-500 dark:bg-accent-400',
                        'bg-accent-400 dark:bg-accent-300',
                        'bg-gray-400 dark:bg-gray-500',
                      ];
                      return (
                        <div key={idx} className="flex items-center gap-2">
                          <span className="text-xs font-bold text-gray-400 dark:text-gray-500 w-4 text-right">{idx + 1}</span>
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-center mb-0.5">
                              <span className="text-xs font-medium text-gray-700 dark:text-gray-300 truncate">{item.type}</span>
                              <span className="text-[10px] font-bold text-gray-500 dark:text-gray-400 ml-1">{item.count}</span>
                            </div>
                            <div className="progress-bar-modern">
                              <div
                                className={`progress-bar-fill ${barColors[idx]}`}
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Quick access */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <button
              onClick={() => navigate('/assets')}
              className="card-modern p-4 text-left hover:border-brand-200 dark:hover:border-brand-700 active:scale-[0.98] transition-all"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-card-sm bg-brand-50 dark:bg-brand-900/20">
                  <Package className="w-5 h-5 text-brand-600 dark:text-brand-400" />
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100 text-sm">Активы</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{stats.total} единиц</p>
                </div>
              </div>
            </button>
            <button
              onClick={() => navigate('/repairs')}
              className="card-modern p-4 text-left hover:border-yellow-200 dark:hover:border-yellow-700 active:scale-[0.98] transition-all"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-card-sm bg-yellow-50 dark:bg-yellow-900/20">
                  <Wrench className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100 text-sm">Ремонты</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{repairStats?.in_progress || 0} в работе</p>
                </div>
              </div>
            </button>
            <button
              onClick={() => navigate('/reports')}
              className="card-modern p-4 text-left hover:border-accent-200 dark:hover:border-accent-700 active:scale-[0.98] transition-all"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-card-sm bg-accent-50 dark:bg-accent-900/20">
                  <Database className="w-5 h-5 text-accent-600 dark:text-accent-400" />
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100 text-sm">Отчёты</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Сводки и аналитика</p>
                </div>
              </div>
            </button>
          </div>
        </main>
      )}
    </div>
  );
};

export default Dashboard;
