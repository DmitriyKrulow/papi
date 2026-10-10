// frontend/src/pages/DisposalPage.tsx
import React, { useState, useEffect } from 'react';

interface DisposalRecord {
  id: number;
  entity_id: number;
  inventory_number?: string;
  asset_name?: string;
  reason?: string;
  disposed_by?: string;
  disposed_at: string;
  diff_summary?: string;
  comment?: string;
  old_values?: any;
  new_values?: any;
}

const DisposalPage: React.FC = () => {
  const [history, setHistory] = useState<DisposalRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/disposal/history', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        const entries = Array.isArray(data.entries) ? data.entries : [];
        const records: DisposalRecord[] = entries.map((e: any) => {
          const newVals = e.new_values || {};
          const oldVals = e.old_values || {};
          return {
            id: e.entity_id,
            entity_id: e.entity_id,
            inventory_number: (oldVals.inventory_number as string) || '',
            asset_name: (oldVals.name as string) || `ID: ${e.entity_id}`,
            reason: e.diff_summary || newVals.reason || '—',
            disposed_by: e.user_name || '—',
            disposed_at: e.created_at || new Date().toISOString(),
            comment: e.comment,
          };
        });
        setHistory(records);
      } else {
        setError(`Ошибка загрузки: ${response.status}`);
      }
    } catch (err) {
      console.error('Failed to fetch disposal history:', err);
      setError('Не удалось загрузить историю списаний');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  if (loading) {
    return <div className="text-center py-8 text-gray-500">Загрузка...</div>;
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg" role="alert">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">🗑️ Списание активов</h2>

      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 border border-gray-100 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">
          История списаний ({history.length})
        </h3>

        {history.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            Записей о списании пока нет
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Инв. номер</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Название</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Причина</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Кто списал</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Дата</th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {history.map((record) => (
                  <tr key={record.id} className="hover:bg-gray-50 dark:hover:bg-gray-750 transition">
                    <td className="px-6 py-4 text-sm font-mono text-gray-900 dark:text-gray-100">{record.inventory_number || '—'}</td>
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">{record.asset_name || '—'}</td>
                    <td className="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">{record.reason || '—'}</td>
                    <td className="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">{record.disposed_by || '—'}</td>
                    <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                      {record.disposed_at ? new Date(record.disposed_at).toLocaleDateString('ru-RU') : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 dark:text-blue-300 mb-2">ℹ️ Дисциплина списания</h3>
        <ul className="text-sm text-blue-800 dark:text-blue-400 space-y-1 list-disc list-inside">
          <li>Списание фиксируется немедленно — актив сразу меняется статус</li>
          <li>Каждая запись содержит причину и ответственного</li>
          <li>Возможно восстановление из списания через API</li>
        </ul>
      </div>
    </div>
  );
};

export default DisposalPage;
