// frontend/src/pages/AnalyticsPage.tsx
import React, { useState, useEffect } from 'react';
import { TrendingUp, Wrench, Loader2, AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface BreakdownTrend {
  type_code: string;
  type_name: string;
  repair_count: number;
  completed_count: number;
  avg_cost: number;
}

interface MonthlyTrend {
  month: string;
  count: number;
}

interface StatusDist {
  status: string;
  count: number;
}

interface BreakdownData {
  top_types: BreakdownTrend[];
  monthly_trend: MonthlyTrend[];
  status_distribution: StatusDist[];
}

const AnalyticsPage: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<BreakdownData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [months, setMonths] = useState(12);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/analytics/breakdown-trends?months=${months}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        setData(null);
        setError(
          res.status === 403
            ? 'Недостаточно прав: аналитика поломок доступна только администраторам.'
            : `Не удалось загрузить данные (HTTP ${res.status}).`,
        );
        return;
      }
      const json = await res.json();
      setData({
        top_types: json.top_types ?? [],
        monthly_trend: json.monthly_trend ?? [],
        status_distribution: json.status_distribution ?? [],
      });
    } catch (e) {
      console.error(e);
      setData(null);
      setError('Сервер недоступен. Проверьте, что backend запущен.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [months]);

  const statusColors: Record<string, string> = {
    draft: '#6B7280', submitted: '#3B82F6', approved: '#6366F1',
    in_progress: '#F59E0B', completed: '#10B981', rejected: '#EF4444', cancelled: '#9CA3AF',
  };

  const statusLabels: Record<string, string> = {
    draft: 'Черновик', submitted: 'Отправлена', approved: 'Одобрена',
    in_progress: 'В работе', completed: 'Завершена', rejected: 'Отклонена', cancelled: 'Отменена',
  };

  const maxTypeCount = data?.top_types[0]?.repair_count || 1;
  const barColors = ['#EF4444', '#F97316', '#F59E0B', '#84CC16', '#22C55E', '#14B8A6', '#3B82F6', '#6366F1', '#8B5CF6', '#EC4899'];

  const hasData = !!data && (
    data.top_types.length > 0 || data.monthly_trend.length > 0 || data.status_distribution.length > 0
  );

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <TrendingUp className="w-7 h-7 text-red-600" />
            📈 Аналитика поломок
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Статистика по типам активов, которые чаще всего требуют ремонта
          </p>
        </div>
        <div className="flex gap-2 items-center">
          <label className="text-sm text-gray-600 dark:text-gray-400">Период:</label>
          <select
            value={months}
            onChange={(e) => setMonths(Number(e.target.value))}
            className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm"
          >
            <option value={3}>3 мес</option>
            <option value={6}>6 мес</option>
            <option value={12}>12 мес</option>
            <option value={24}>24 мес</option>
          </select>
          <button onClick={() => navigate('/dashboard')} className="text-blue-600 hover:text-blue-800 dark:text-blue-400 text-sm">
            ← Назад на дашборд
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center py-16">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <span className="ml-3 text-gray-500">Загрузка...</span>
        </div>
      ) : error ? (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 flex flex-col items-start gap-3">
          <div className="flex items-center gap-2 text-red-700 dark:text-red-300">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm font-medium">{error}</span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={fetchData}
              className="px-3 py-1.5 text-sm rounded-lg bg-red-600 text-white hover:bg-red-700 transition"
            >
              Повторить
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="px-3 py-1.5 text-sm rounded-lg border border-red-300 dark:border-red-700 text-red-700 dark:text-red-300 hover:bg-red-100 dark:hover:bg-red-900/40 transition"
            >
              На дашборд
            </button>
          </div>
        </div>
      ) : hasData ? (
        <>
          {/* Топ-10 типов активов по ремонтам */}
          {data.top_types.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                <Wrench className="w-5 h-5 text-red-600" />
                Топ-10 типов активов по количеству ремонтов
              </h2>
              <div className="space-y-3">
                {data.top_types.map((t, i) => (
                  <div key={t.type_code}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {t.type_name || t.type_code}
                      </span>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 dark:text-gray-400">
                          {t.completed_count}/{t.repair_count} завершено
                        </span>
                        {t.avg_cost > 0 && (
                          <span className="text-gray-500 dark:text-gray-400">
                            ~{Math.round(t.avg_cost).toLocaleString('ru-RU')} ₽
                          </span>
                        )}
                        <span className="font-bold text-gray-900 dark:text-gray-100">{t.repair_count}</span>
                      </div>
                    </div>
                    <div className="w-full bg-gray-100 dark:bg-gray-700 rounded-full h-2.5">
                      <div
                        className="h-2.5 rounded-full transition-all duration-500"
                        style={{
                          width: `${(t.repair_count / maxTypeCount) * 100}%`,
                          backgroundColor: barColors[i % barColors.length],
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Помесячный тренд */}
            {data.monthly_trend.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-blue-600" />
                  Динамика ремонтов по месяцам
                </h3>
                <div className="space-y-2">
                  {data.monthly_trend.map((m) => {
                    const maxCount = Math.max(...data.monthly_trend.map(x => x.count), 1);
                    const pct = (m.count / maxCount) * 100;
                    return (
                      <div key={m.month} className="flex items-center gap-2">
                        <span className="text-xs text-gray-500 dark:text-gray-400 w-10 text-right">{m.month}</span>
                        <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-4 relative overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-500"
                            style={{ width: `${pct}%` }}
                          />
                          <span className="absolute inset-0 flex items-center justify-end pr-2 text-xs font-medium text-white drop-shadow">
                            {m.count}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Распределение по статусам */}
            {data.status_distribution.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                  Распределение по статусам
                </h3>
                <div className="space-y-2">
                  {data.status_distribution.map((s) => {
                    const total = data.status_distribution.reduce((sum, x) => sum + x.count, 0);
                    const pct = total > 0 ? Math.round((s.count / total) * 100) : 0;
                    return (
                      <div key={s.status} className="flex items-center gap-3">
                        <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: statusColors[s.status] || '#6B7280' }} />
                        <span className="text-sm text-gray-600 dark:text-gray-400 flex-1 truncate">
                          {statusLabels[s.status] || s.status}
                        </span>
                        <span className="text-sm font-bold text-gray-900 dark:text-gray-100">{s.count}</span>
                        <span className="text-xs text-gray-400 w-10 text-right">{pct}%</span>
                      </div>
                    );
                  })}
                </div>
                {/* Прогресс-бар общего распределения */}
                <div className="flex rounded-full overflow-hidden h-3 mt-4 gap-0.5">
                  {data.status_distribution.map((s) => {
                    const total = data.status_distribution.reduce((sum, x) => sum + x.count, 0);
                    const pct = total > 0 ? (s.count / total) * 100 : 0;
                    return (
                      <div
                        key={s.status}
                        className="h-full transition-all duration-500"
                        style={{
                          width: `${pct}%`,
                          backgroundColor: statusColors[s.status] || '#6B7280',
                        }}
                        title={`${statusLabels[s.status] || s.status}: ${s.count}`}
                      />
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Итого */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                {data.top_types.reduce((sum, t) => sum + t.repair_count, 0)}
              </div>
              <div className="text-sm text-red-700 dark:text-red-300">Всего ремонтов</div>
            </div>
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {data.top_types.reduce((sum, t) => sum + t.completed_count, 0)}
              </div>
              <div className="text-sm text-green-700 dark:text-green-300">Завершено</div>
            </div>
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {data.top_types.length}
              </div>
              <div className="text-sm text-blue-700 dark:text-blue-300">Типов активов</div>
            </div>
            <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
              <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {months} мес
              </div>
              <div className="text-sm text-purple-700 dark:text-purple-300">Период анализа</div>
            </div>
          </div>
        </>
      ) : (
        <div className="bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-12 text-center">
          <div className="text-5xl mb-4">📊</div>
          <h3 className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-2">
            Нет данных для отображения
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-6 max-w-md mx-auto">
            За выбранный период заявок на ремонт не зафиксировано.
            Попробуйте расширить период или перейдите к списку ремонтов.
          </p>
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={() => setMonths(24)}
              className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition"
            >
              Показать за 24 мес
            </button>
            <button
              onClick={() => navigate('/repairs')}
              className="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition"
            >
              Список ремонтов
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalyticsPage;
