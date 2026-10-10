// frontend/src/pages/ReconciliationPage.tsx
import React, { useState, useEffect } from 'react';

interface ReconciliationItem {
  id: number;
  month: string;
  department_code: string;
  department_name: string;
  status: string;
  total_assets: number;
  matched: number;
  unmatched: number;
  created_at: string;
}

const ReconciliationPage: React.FC = () => {
  const [records, setRecords] = useState<ReconciliationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear().toString());

  const fetchRecords = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/reconciliation/history?year=${selectedYear}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setRecords(data.records || data || []);
      }
    } catch (err) {
      console.error('Failed to fetch reconciliation:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, [selectedYear]);

  if (loading) {
    return <div className="text-center py-8 text-gray-500">Загрузка...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">🔄 Ежемесячная сверка</h2>
        <select
          value={selectedYear}
          onChange={(e) => setSelectedYear(e.target.value)}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
        >
          {[2024, 2025, 2026].map(y => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
      </div>

      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 border border-gray-100 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">
          История сверок ({records.length})
        </h3>

        {records.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            Сверок за {selectedYear} год не найдено
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Месяц</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Подразделение</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Всего</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Совпало</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Расхождения</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Статус</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Дата</th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {records.map((record) => (
                  <tr key={record.id} className="hover:bg-gray-50 dark:hover:bg-gray-750 transition">
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">
                      {new Date(record.month + '-01').toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">{record.department_name || record.department_code}</td>
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">{record.total_assets}</td>
                    <td className="px-6 py-4 text-sm text-green-700 dark:text-green-300">{record.matched}</td>
                    <td className="px-6 py-4 text-sm text-red-700 dark:text-red-300">{record.unmatched}</td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        record.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' :
                        record.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300' :
                        'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300'
                      }`}>
                        {record.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                      {new Date(record.created_at).toLocaleDateString('ru-RU')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 dark:text-blue-300 mb-2">ℹ️ Ежемесячная сверка с бухгалтерией</h3>
        <ul className="text-sm text-blue-800 dark:text-blue-400 space-y-1 list-disc list-inside">
          <li>Сверка автоматически reconciles данные инвентаризаций с бухгалтерией</li>
          <li>Результаты можно экспортировать в Excel для отчётности</li>
          <li>Расхождения отображаются для каждого подразделения</li>
        </ul>
      </div>
    </div>
  );
};

export default ReconciliationPage;
