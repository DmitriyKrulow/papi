// frontend/src/pages/Dashboard.tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { ClipboardCheck, CheckCircle2, Clock, Loader2, Wrench, TrendingUp } from 'lucide-react';

interface Stats {
  total: number;
  active: number;
  maintenance: number;
  written_off: number;
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
  const [dbStatus, setDbStatus] = useState<string>('checking...');
  const [dbDetails, setDbDetails] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<Stats>({
    total: 0,
    active: 0,
    maintenance: 0,
    written_off: 0,
  });
  const [activeInventory, setActiveInventory] = useState<InventoryCheck | null>(null);
  const [inventoryLoading, setInventoryLoading] = useState(false);
  const [repairStats, setRepairStats] = useState<RepairStats | null>(null);
  const [repairStatsLoading, setRepairStatsLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const dbResponse = await fetch('/api/db-check');
        
        if (dbResponse.ok) {
          const data = await dbResponse.json();
          if (data && data.status === 'connected') {
            setDbStatus('connected');
            setDbDetails(data.database || 'papiBD');
          } else {
            setDbStatus('disconnected');
            setDbDetails(data?.error || 'Неизвестная ошибка');
          }
        } else {
          setDbStatus('disconnected');
          setDbDetails('Ошибка подключения');
        }
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
            });
          }
        } else {
          // Статистика не загружена — используем пустые значения
        }

        // Загрузка активной инвентаризации
        setInventoryLoading(true);
        const invResponse = await fetch('/api/inventory-checks/active', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        });
        
        if (invResponse.ok) {
          const invData = await invResponse.json();
          setActiveInventory(invData);
        }
        
        setInventoryLoading(false);

        // Загрузка статистики ремонтов
        setRepairStatsLoading(true);
        try {
          const repairResponse = await fetch('/api/repairs/stats/', {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
            },
          });
          if (repairResponse.ok) {
            const repairData = await repairResponse.json();
            setRepairStats(repairData);
          }
        } catch {
          // Статистика ремонтов не загружена
        } finally {
          setRepairStatsLoading(false);
        }
        
        setLoading(false);
      } catch (err: any) {
        setDbStatus('disconnected');
        setDbDetails(err.message || 'Ошибка соединения');
        setLoading(false);
      }
    };
    
    fetchData();
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Загрузка...</h2>
        </div>
      </div>
    );
  }

  const statCards = [
    { 
      label: 'Всего активов', 
      value: stats.total, 
      color: 'blue',
      icon: '📦',
    },
    { 
      label: 'Активных', 
      value: stats.active, 
      color: 'green',
      icon: '✅',
    },
    { 
      label: 'На ремонте', 
      value: stats.maintenance, 
      color: 'yellow',
      icon: '🔧',
    },
    { 
      label: 'Списано', 
      value: stats.written_off, 
      color: 'red',
      icon: '📄',
    },
  ];

  const colorClasses = {
    blue: 'text-blue-600 dark:text-blue-400',
    green: 'text-green-600 dark:text-green-400',
    yellow: 'text-yellow-600 dark:text-yellow-400',
    red: 'text-red-600 dark:text-red-400',
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      <main className="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {loading ? (
          <div className="flex justify-center items-center py-16">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent"></div>
              <p className="mt-4 text-gray-500 dark:text-gray-400 text-lg">Загрузка данных...</p>
            </div>
          </div>
        ) : (
          <>
            <div className="text-center mb-6 sm:mb-8">
              <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2">📊 Дашборд</h1>
              <p className="text-gray-500 dark:text-gray-400">Обзор системы управления активами</p>
            </div>

            <div className="mb-6 p-4 bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-100 dark:border-gray-700">
              <div className="flex items-center space-x-2 flex-wrap">
                <span className="font-medium text-gray-700 dark:text-gray-300">Статус БД:</span>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    dbStatus === 'connected'
                      ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                      : dbStatus === 'checking...'
                      ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
                      : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                  }`}
                >
                  {dbStatus === 'connected' ? '✅ Подключена' :
                   dbStatus === 'checking...' ? '⏳ Проверка...' :
                   '❌ Отключена'}
                </span>
                {dbDetails && (
                  <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">
                    ({dbDetails})
                  </span>
                )}
              </div>
              {error && (
                <div className="mt-2 text-sm text-red-600 dark:text-red-400">
                  Ошибка: {error}
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 md:gap-6">
              {statCards.map((stat) => (
                <div key={stat.label} className="bg-white dark:bg-gray-800 rounded-lg shadow p-3 sm:p-4 md:p-6 hover:shadow-lg transition border border-gray-100 dark:border-gray-700 active:scale-95 transition-transform">
                  <div className="flex items-center justify-between mb-1 sm:mb-2">
                    <div className="text-xl sm:text-2xl">{stat.icon}</div>
                    <div className={`text-lg sm:text-xl md:text-2xl font-bold ${colorClasses[stat.color as keyof typeof colorClasses]}`}>
                      {stat.value}
                    </div>
                  </div>
                  <div className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 truncate">{stat.label}</div>
                </div>
              ))}
            </div>

            {/* Блок активной инвентаризации */}
            {inventoryLoading ? (
              <div className="mt-6 sm:mt-8 bg-white dark:bg-gray-800 rounded-lg shadow p-4 sm:p-6 border border-gray-100 dark:border-gray-700">
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-blue-600 dark:text-blue-400" />
                  <span className="ml-2 text-gray-500 dark:text-gray-400">Загрузка данных инвентаризации...</span>
                </div>
              </div>
            ) : activeInventory ? (
              <div className="mt-6 sm:mt-8 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg shadow p-4 sm:p-6 border-2 border-blue-200 dark:border-blue-700">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-600 dark:bg-blue-700 rounded-lg">
                      <ClipboardCheck className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-blue-900 dark:text-blue-100">{activeInventory.name}</h3>
                      <p className="text-sm text-blue-700 dark:text-blue-300">
                        {activeInventory.check_type === 'full' ? 'Полная инвентаризация' : 
                         activeInventory.check_type === 'by_room' ? 'По помещениям' :
                         activeInventory.check_type === 'by_employee' ? 'По сотрудникам' :
                         'По ответственному лицу'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 dark:bg-blue-700 text-white rounded-full text-sm font-medium">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    В процессе
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                  <div className="bg-white dark:bg-gray-800 rounded-lg p-3 shadow-sm">
                    <div className="flex items-center gap-2 mb-1">
                      <Clock className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                      <span className="text-xs text-gray-500 dark:text-gray-400">Начата</span>
                    </div>
                    <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      {activeInventory.started_at ? new Date(activeInventory.started_at).toLocaleDateString('ru-RU') : '—'}
                    </p>
                  </div>

                  <div className="bg-white dark:bg-gray-800 rounded-lg p-3 shadow-sm">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg">📦</span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">Всего</span>
                    </div>
                    <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{activeInventory.total_checked}</p>
                  </div>

                  <div className="bg-white dark:bg-gray-800 rounded-lg p-3 shadow-sm">
                    <div className="flex items-center gap-2 mb-1">
                      <CheckCircle2 className="w-4 h-4 text-green-600 dark:text-green-400" />
                      <span className="text-xs text-gray-500 dark:text-gray-400">Найдено</span>
                    </div>
                    <p className="text-lg font-bold text-green-600 dark:text-green-400">{activeInventory.found}</p>
                  </div>

                  <div className="bg-white dark:bg-gray-800 rounded-lg p-3 shadow-sm">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg">❌</span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">Отсутствует</span>
                    </div>
                    <p className="text-lg font-bold text-red-600 dark:text-red-400">{activeInventory.missing}</p>
                  </div>
                </div>

                {/* Прогресс-бар */}
                <div className="mt-4">
                  <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                    <span>Прогресс проверки</span>
                    <span>
                      {activeInventory.total_checked > 0 
                        ? Math.round(((activeInventory.found + activeInventory.missing) / activeInventory.total_checked) * 100) 
                        : 0}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                    <div
                      className="bg-blue-600 dark:bg-blue-500 h-2.5 rounded-full transition-all duration-500"
                      style={{
                        width: `${activeInventory.total_checked > 0 
                          ? ((activeInventory.found + activeInventory.missing) / activeInventory.total_checked) * 100 
                          : 0}%`,
                      }}
                    ></div>
                  </div>
                </div>

                {/* Список активов */}
                {activeInventory.items && activeInventory.items.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-semibold text-blue-800 dark:text-blue-200 mb-2">
                      Проверяемые активы ({activeInventory.items.length})
                    </h4>
                    <div className="max-h-60 overflow-y-auto space-y-1.5 pr-1 custom-scrollbar">
                      {activeInventory.items.map((item) => (
                        <div
                          key={item.id}
                          className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs transition ${
                            item.result === 'found'
                              ? 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/10'
                              : item.result === 'missing'
                              ? 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10'
                              : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50'
                          }`}
                        >
                          {item.result === 'found' ? (
                            <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                          ) : item.result === 'missing' ? (
                            <Clock className="w-4 h-4 text-red-400 flex-shrink-0" />
                          ) : (
                            <Clock className="w-4 h-4 text-gray-400 flex-shrink-0" />
                          )}
                          <div className="flex-1 min-w-0">
                            <span className="font-mono text-gray-500 dark:text-gray-400">
                              {item.inventory_number}
                            </span>
                            <span className="ml-2 font-medium text-gray-800 dark:text-gray-200 truncate">
                              {item.asset_name}
                            </span>
                          </div>
                          <div className="flex-shrink-0 text-xs text-gray-400 dark:text-gray-500">
                            {item.model && <span className="mr-2">{item.model}</span>}
                            {item.location && <span>📍 {item.location}</span>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="mt-4 flex gap-2">
                  <button
                    onClick={() => navigate('/inventory')}
                    className="flex-1 px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 transition text-sm font-medium"
                  >
                    Перейти к инвентаризации
                  </button>
                  <button
                    onClick={() => navigate('/assets')}
                    className="flex-1 px-4 py-2 bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-700 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition text-sm font-medium"
                  >
                    Смотреть активы
                  </button>
                </div>
              </div>
            ) : (
              <div className="mt-6 sm:mt-8 bg-white dark:bg-gray-800 rounded-lg shadow p-4 sm:p-6 border border-gray-100 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                      <ClipboardCheck className="w-6 h-6 text-gray-500 dark:text-gray-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Инвентаризация</h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Нет активных проверок</p>
                    </div>
                  </div>
                  <button
                    onClick={() => navigate('/inventory')}
                    className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition text-sm font-medium"
                  >
                    Создать инвентаризацию
                  </button>
                </div>
              </div>
            )}

            {/* Статистика ремонтов */}
            {repairStats && (
              <div className="mt-6 sm:mt-8 grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
                {/* Карточки */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 sm:p-6 border border-gray-100 dark:border-gray-700">
                  <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2">
                    <Wrench className="w-5 h-5 text-orange-600 dark:text-orange-400" />
                    🔧 Заявки на ремонт
                  </h3>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-3">
                      <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">{repairStats.total_repairs}</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">Всего заявок</div>
                    </div>
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">
                      <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{repairStats.in_progress}</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">В работе</div>
                    </div>
                    <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3">
                      <div className="text-2xl font-bold text-green-600 dark:text-green-400">{repairStats.completed}</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">Завершено</div>
                    </div>
                    <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-3">
                      <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">{repairStats.active_repair_assets}</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">Активов в ремонте</div>
                    </div>
                  </div>
                  <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700 flex justify-between items-center text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Смета:</span>
                    <span className="font-bold text-gray-800 dark:text-gray-200">{repairStats.total_estimated_cost.toLocaleString('ru-RU')} ₽</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Факт:</span>
                    <span className="font-bold text-gray-800 dark:text-gray-200">{repairStats.total_actual_cost.toLocaleString('ru-RU')} ₽</span>
                  </div>
                </div>

                {/* Топ-5 типов активов */}
                {repairStats.top_asset_types.length > 0 && (
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 sm:p-6 border border-gray-100 dark:border-gray-700">
                    <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2">
                      <TrendingUp className="w-5 h-5 text-red-600 dark:text-red-400" />
                      🔥 Топ-5 типов активов по ремонтам
                    </h3>
                    <div className="space-y-3">
                      {repairStats.top_asset_types.map((item, idx) => {
                        const maxCount = repairStats.top_asset_types[0]?.count || 1;
                        const pct = Math.round((item.count / maxCount) * 100);
                        const colors = [
                          'bg-red-500 dark:bg-red-400',
                          'bg-orange-500 dark:bg-orange-400',
                          'bg-yellow-500 dark:bg-yellow-400',
                          'bg-green-500 dark:bg-green-400',
                          'bg-blue-500 dark:bg-blue-400',
                        ];
                        return (
                          <div key={idx} className="flex items-center gap-3">
                            <span className="text-xs font-bold text-gray-500 dark:text-gray-400 w-5 text-right">{idx + 1}</span>
                            <div className="flex-1 min-w-0">
                              <div className="flex justify-between items-center mb-1">
                                <span className="text-sm font-medium text-gray-700 dark:text-gray-300 truncate">{item.type}</span>
                                <span className="text-xs font-bold text-gray-600 dark:text-gray-400 ml-2">{item.count}</span>
                              </div>
                              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                <div
                                  className={`h-2 rounded-full ${colors[idx]}`}
                                  style={{ width: `${pct}%` }}
                                ></div>
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

            {/* Дополнительная информация */}
            <div className="mt-6 sm:mt-8 grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 sm:p-6 border border-gray-100 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">📈 Общая статистика</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center border-b border-gray-100 dark:border-gray-700 pb-2">
                    <span className="text-gray-600 dark:text-gray-400">Всего активов:</span>
                    <span className="font-bold text-blue-600 dark:text-blue-400">{stats.total}</span>
                  </div>
                  <div className="flex justify-between items-center border-b border-gray-100 dark:border-gray-700 pb-2">
                    <span className="text-gray-600 dark:text-gray-400">Активных:</span>
                    <span className="font-bold text-green-600 dark:text-green-400">{stats.active}</span>
                  </div>
                  <div className="flex justify-between items-center border-b border-gray-100 dark:border-gray-700 pb-2">
                    <span className="text-gray-600 dark:text-gray-400">На ремонте:</span>
                    <span className="font-bold text-yellow-600 dark:text-yellow-400">{stats.maintenance}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600 dark:text-gray-400">Списано:</span>
                    <span className="font-bold text-red-600 dark:text-red-400">{stats.written_off}</span>
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 sm:p-6 border border-gray-100 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">🔍 Быстрый доступ</h3>
                <div className="space-y-3">
                  <button
                    onClick={() => navigate('/assets')}
                    className="w-full text-left px-4 py-3 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/50 transition active:scale-95 transition-transform"
                  >
                    📦 Перейти к активам
                  </button>
                  <button
                    onClick={() => navigate('/repairs')}
                    className="w-full text-left px-4 py-3 bg-orange-50 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 rounded-lg hover:bg-orange-100 dark:hover:bg-orange-900/50 transition active:scale-95 transition-transform"
                  >
                    🔧 Заявки на ремонт
                  </button>
                  <button
                    onClick={() => navigate('/reports')}
                    className="w-full text-left px-4 py-3 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/50 transition active:scale-95 transition-transform"
                  >
                    📊 Перейти к отчетам
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
