import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { auditApi } from '../api/audit';
import {
  Search,
  Filter,
  Clock,
  User,
  Calendar,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  FileText,
  Eye,
  Loader2,
  BarChart3,
  RefreshCw,
} from 'lucide-react';

interface AuditEntry {
  id: number;
  created_at: string;
  user_name: string | null;
  ip_address: string | null;
  method: string | null;
  entity_type: string;
  entity_id: number;
  action: string;
  diff_summary: string | null;
  comment: string | null;
}

interface AuditSummary {
  total: number;
  by_action: Record<string, number>;
  by_entity_type: Record<string, number>;
  last_entries: AuditEntry[];
}

interface AuditStats {
  today: number;
  last_7_days: number;
  last_30_days: number;
  top_active_users_today: Array<{ user_id: number; actions: number }>;
}

const ACTION_LABELS: Record<string, string> = {
  create: 'Создание',
  update: 'Изменение',
  delete: 'Удаление',
  login: 'Вход',
  logout: 'Выход',
  status_change: 'Смена статуса',
  import: 'Импорт',
  export: 'Экспорт',
  inventory_start: 'Начало инвентаризации',
  inventory_complete: 'Завершение инвентаризации',
  repair_create: 'Создание заявки',
  repair_update: 'Обновление заявки',
};

const ACTION_ICONS: Record<string, string> = {
  create: '➕',
  update: '✏️',
  delete: '🗑️',
  login: '🔑',
  logout: '🚪',
  status_change: '🔄',
  import: '📥',
  export: '📤',
  inventory_start: '📋',
  inventory_complete: '✅',
  repair_create: '🔧',
  repair_update: '🔧',
};

const ENTITY_LABELS: Record<string, string> = {
  Asset: 'Актив',
  User: 'Пользователь',
  RepairRequest: 'Заявка на ремонт',
  InventoryCheck: 'Инвентаризация',
};

const AuditLogPage: React.FC = () => {
  const { isAuthenticated, user } = useAuth();
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [summary, setSummary] = useState<AuditSummary | null>(null);
  const [stats, setStats] = useState<AuditStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const limit = 50;

  // Фильтры
  const [showFilters, setShowFilters] = useState(false);
  const [entityType, setEntityType] = useState('');
  const [action, setAction] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const isAdmin = user?.role === 'admin';

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [data, sumData, statsData] = await Promise.all([
        auditApi.getAll({
          limit,
          offset: (page - 1) * limit,
          entity_type: entityType || undefined,
          action: action || undefined,
        }),
        auditApi.getSummary(),
        auditApi.getStatsOverview(),
      ]);
      setEntries(data.items || []);
      setTotal(data.total || 0);
      setSummary(sumData);
      setStats(statsData);
    } catch (err) {
      console.error('Failed to load audit log:', err);
    } finally {
      setLoading(false);
    }
  }, [page, entityType, action]);

  useEffect(() => {
    if (isAuthenticated && isAdmin) {
      fetchData();
    }
  }, [isAuthenticated, isAdmin, fetchData]);

  const totalPages = Math.ceil(total / limit);

  if (!isAuthenticated || !isAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center p-8">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Доступ запрещён
          </h2>
          <p className="text-gray-500 dark:text-gray-400">
            Журнал аудита доступен только для администраторов
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      <main className="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {/* Заголовок */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-4">
          <div>
            <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-1">
              📜 Журнал аудита
            </h1>
            <p className="text-gray-500 dark:text-gray-400">
              История всех значимых действий в системе
            </p>
          </div>
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition text-sm"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Обновить
          </button>
        </div>

        {/* Статистика за периоды */}
        {stats && (
          <div className="grid grid-cols-3 gap-3 sm:gap-4 mb-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-2 mb-1">
                <Calendar className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <span className="text-xs text-gray-500 dark:text-gray-400">Сегодня</span>
              </div>
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats.today}</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-2 mb-1">
                <Clock className="w-4 h-4 text-green-600 dark:text-green-400" />
                <span className="text-xs text-gray-500 dark:text-gray-400">7 дней</span>
              </div>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.last_7_days}</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-2 mb-1">
                <BarChart3 className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                <span className="text-xs text-gray-500 dark:text-gray-400">30 дней</span>
              </div>
              <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">{stats.last_30_days}</p>
            </div>
          </div>
        )}

        {/* Сводка по действиям и сущностям */}
        {summary && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-100 dark:border-gray-700">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                По действиям
              </h3>
              <div className="flex flex-wrap gap-2">
                {Object.entries(summary.by_action).map(([act, count]) => (
                  <button
                    key={act}
                    onClick={() => {
                      setAction(action === act ? '' : act);
                      setPage(1);
                    }}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                      action === act
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                    }`}
                  >
                    {ACTION_LABELS[act] || act}
                    <span className="ml-1 opacity-70">{count}</span>
                  </button>
                ))}
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-100 dark:border-gray-700">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                По сущностям
              </h3>
              <div className="flex flex-wrap gap-2">
                {Object.entries(summary.by_entity_type).map(([entity, count]) => (
                  <button
                    key={entity}
                    onClick={() => {
                      setEntityType(entityType === entity ? '' : entity);
                      setPage(1);
                    }}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                      entityType === entity
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                    }`}
                  >
                    {ENTITY_LABELS[entity] || entity}
                    <span className="ml-1 opacity-70">{count}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Фильтры */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow mb-6 border border-gray-100 dark:border-gray-700">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="w-full flex items-center justify-between p-4 text-left"
          >
            <span className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300">
              <Filter className="w-4 h-4" />
              Фильтры
            </span>
            <Filter className="w-4 h-4 text-gray-400 transition-transform" />
          </button>

          {showFilters && (
            <div className="px-4 pb-4 border-t border-gray-100 dark:border-gray-700 pt-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                    Поиск
                  </label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type="text"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      placeholder="Комментарий..."
                      className="w-full pl-10 pr-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-sm text-gray-900 dark:text-gray-100"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                    Тип сущности
                  </label>
                  <select
                    value={entityType}
                    onChange={(e) => { setEntityType(e.target.value); setPage(1); }}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-sm text-gray-900 dark:text-gray-100"
                  >
                    <option value="">Все</option>
                    {Object.entries(ENTITY_LABELS).map(([key, label]) => (
                      <option key={key} value={key}>{label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                    Действие
                  </label>
                  <select
                    value={action}
                    onChange={(e) => { setAction(e.target.value); setPage(1); }}
                    className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-sm text-gray-900 dark:text-gray-100"
                  >
                    <option value="">Все</option>
                    {Object.entries(ACTION_LABELS).map(([key, label]) => (
                      <option key={key} value={key}>{label}</option>
                    ))}
                  </select>
                </div>
                <div className="flex items-end">
                  <button
                    onClick={() => {
                      setEntityType('');
                      setAction('');
                      setSearchTerm('');
                      setPage(1);
                    }}
                    className="w-full px-3 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg text-sm hover:bg-gray-200 dark:hover:bg-gray-600 transition"
                  >
                    Сбросить
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Таблица */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-100 dark:border-gray-700 overflow-hidden">
          {loading ? (
            <div className="flex justify-center items-center py-16">
              <div className="text-center">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-3" />
                <p className="text-gray-500 dark:text-gray-400">Загрузка журнала...</p>
              </div>
            </div>
          ) : entries.length === 0 ? (
            <div className="flex justify-center items-center py-16">
              <div className="text-center">
                <FileText className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                <p className="text-gray-500 dark:text-gray-400">Записей не найдено</p>
              </div>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-900/50 border-b border-gray-100 dark:border-gray-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Дата/Время
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Пользователь
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Действие
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Сущность
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Изменения
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase hidden sm:table-cell">
                        IP
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                    {entries.map((entry) => (
                      <tr
                        key={entry.id}
                        className="hover:bg-gray-50 dark:hover:bg-gray-900/50 transition"
                      >
                        <td className="px-4 py-3">
                          <div className="text-sm text-gray-900 dark:text-gray-100 font-medium">
                            {new Date(entry.created_at).toLocaleDateString('ru-RU')}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {new Date(entry.created_at).toLocaleTimeString('ru-RU', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <User className="w-3.5 h-3.5 text-gray-400" />
                            <span className="text-sm text-gray-900 dark:text-gray-100">
                              {entry.user_name || '—'}
                            </span>
                          </div>
                          {entry.method && (
                            <span className={`inline-block px-1.5 py-0.5 text-[10px] font-mono rounded ${
                              entry.method === 'POST' ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
                              entry.method === 'PUT' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' :
                              entry.method === 'PATCH' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300' :
                              entry.method === 'DELETE' ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' :
                              'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                            }`}>
                              {entry.method}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-sm text-gray-900 dark:text-gray-100">
                            {ACTION_ICONS[entry.action] || '📌'}{' '}
                            {ACTION_LABELS[entry.action] || entry.action}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-sm text-gray-900 dark:text-gray-100">
                            {ENTITY_LABELS[entry.entity_type] || entry.entity_type}
                            <span className="text-gray-500 dark:text-gray-400 ml-1">
                              #{entry.entity_id}
                            </span>
                          </span>
                        </td>
                        <td className="px-4 py-3 max-w-xs">
                          <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                            {entry.diff_summary || entry.comment || '—'}
                          </p>
                        </td>
                        <td className="px-4 py-3 hidden sm:table-cell">
                          <span className="text-xs font-mono text-gray-500 dark:text-gray-400">
                            {entry.ip_address || '—'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Пагинация */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 dark:border-gray-700">
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Всего: {total.toLocaleString('ru-RU')} записей
                  </p>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="flex items-center gap-1 px-3 py-1.5 border border-gray-200 dark:border-gray-700 rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ChevronLeft className="w-4 h-4" />
                      Назад
                    </button>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      Страница {page} из {totalPages}
                    </span>
                    <button
                      onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                      className="flex items-center gap-1 px-3 py-1.5 border border-gray-200 dark:border-gray-700 rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Вперёд
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
};

export default AuditLogPage;
