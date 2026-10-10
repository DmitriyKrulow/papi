// frontend/src/pages/HandoversPage.tsx
import React, { useState, useEffect } from 'react';

interface HandoverItem {
  id: number;
  asset_id: number;
  inventory_number: string;
  asset_name: string;
  rfid_tag: string;
  from: string;
  from_user_id: number;
  to: string;
  to_user_id: number;
  department: string;
  reason: string;
  created_at: string;
  return_deadline: string;
  is_overdue: boolean;
  days_overdue: number;
}

interface HandoverStats {
  total_active: number;
  overdue: number;
}

const HandoversPage: React.FC = () => {
  const [activeHandovers, setActiveHandovers] = useState<HandoverItem[]>([]);
  const [stats, setStats] = useState<HandoverStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState<'all' | 'overdue'>('all');

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const [handoversRes, statsRes] = await Promise.all([
        fetch('/api/handovers/all-active', { headers: { 'Authorization': `Bearer ${token}` } }),
        fetch('/api/handovers/stats', { headers: { 'Authorization': `Bearer ${token}` } }),
      ]);
      
      if (handoversRes.ok) {
        const data = await handoversRes.json();
        setActiveHandovers(data.handovers || []);
      }
      if (statsRes.ok) {
        const data = await statsRes.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch handovers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredHandovers = activeFilter === 'overdue' 
    ? activeHandovers.filter(h => h.is_overdue)
    : activeHandovers;

  if (loading) {
    return <div className="text-center py-8 text-gray-500">Загрузка...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="text-2xl font-bold text-blue-900 dark:text-blue-300">{stats.total_active}</div>
            <div className="text-sm text-blue-700 dark:text-blue-400">Активных передач</div>
          </div>
          <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div className="text-2xl font-bold text-red-900 dark:text-red-300">{stats.overdue}</div>
            <div className="text-sm text-red-700 dark:text-red-400">Просрочено</div>
          </div>
          <div className="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-900 dark:text-green-300">
              {stats.total_active - stats.overdue}
            </div>
            <div className="text-sm text-green-700 dark:text-green-400">В срок</div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-900/30 border border-gray-200 dark:border-gray-800 rounded-lg p-4">
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-300">
              {stats.total_active > 0 ? Math.round((stats.overdue / stats.total_active) * 100) : 0}%
            </div>
            <div className="text-sm text-gray-700 dark:text-gray-400">Процент просрочки</div>
          </div>
        </div>
      )}

      {/* Filter */}
      <div className="flex gap-2">
        <button
          onClick={() => setActiveFilter('all')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeFilter === 'all' 
              ? 'bg-blue-600 text-white' 
              : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
          }`}
        >
          Все активные ({activeHandovers.length})
        </button>
        <button
          onClick={() => setActiveFilter('overdue')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeFilter === 'overdue' 
              ? 'bg-red-600 text-white' 
              : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
          }`}
        >
          ⚠️ Просрочено ({stats?.overdue || 0})
        </button>
      </div>

      {/* Handovers Table */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 border border-gray-100 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">
          📦 Активные передачи имущества
        </h2>

        {filteredHandovers.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            {activeFilter === 'overdue' 
              ? '✅ Нет просроченных передач!' 
              : 'Нет активных передач'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Актив</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">RFID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Отдал</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Получил</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Подразделение</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Срок возврата</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Статус</th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {filteredHandovers.map((h) => (
                  <tr key={h.id} className={`hover:bg-gray-50 dark:hover:bg-gray-750 transition ${h.is_overdue ? 'bg-red-50 dark:bg-red-900/20' : ''}`}>
                    <td className="px-6 py-4 text-sm">
                      <div className="font-medium text-gray-900 dark:text-gray-100">{h.asset_name}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">{h.inventory_number}</div>
                    </td>
                    <td className="px-6 py-4 text-sm font-mono text-gray-500 dark:text-gray-400">
                      {h.rfid_tag || '—'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">{h.from}</td>
                    <td className="px-6 py-4 text-sm font-medium text-gray-900 dark:text-gray-100">{h.to}</td>
                    <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">{h.department || '—'}</td>
                    <td className="px-6 py-4 text-sm">
                      {h.return_deadline ? (
                        <div>
                          <div>{new Date(h.return_deadline).toLocaleDateString('ru-RU')}</div>
                          <div className="text-xs text-gray-400">
                            {new Date(h.return_deadline).toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'})}
                          </div>
                        </div>
                      ) : (
                        <span className="text-gray-400">Навсегда</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {h.is_overdue ? (
                        <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300 font-medium">
                          ⚠️ Просрочено ({h.days_overdue} дн.)
                        </span>
                      ) : (
                        <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">
                          В срок
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 dark:text-blue-300 mb-2">ℹ️ Как работает система передач</h3>
        <ul className="text-sm text-blue-800 dark:text-blue-400 space-y-1 list-disc list-inside">
          <li>Каждая передача фиксируется: кто, кому, когда и зачем передал</li>
          <li>При передаче можно указать срок возврата</li>
          <li>Просроченные передачи подсвечиваются красным</li>
          <li>Получатель получает уведомление о передаче</li>
          <li>Вся история передач хранится для каждого актива</li>
          <li>Через RFID-сканер можно автоматически фиксировать передачи</li>
        </ul>
      </div>
    </div>
  );
};

export default HandoversPage;
