// frontend/src/pages/AnalyticsPage.tsx
import React, { useState, useEffect } from 'react';

interface AnalyticsOverview {
  total_assets: number;
  active_assets: number;
  maintenance: number;
  written_off: number;
  total_value: number;
  depreciation: number;
}

const AnalyticsPage: React.FC = () => {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchOverview = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/analytics/overview', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setOverview(data);
      }
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  if (loading) {
    return <div className="text-center py-8 text-gray-500">Загрузка...</div>;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">📊 Аналитика</h2>

      {overview && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-900 dark:text-blue-300">{overview.total_assets}</div>
              <div className="text-sm text-blue-700 dark:text-blue-400">Всего активов</div>
            </div>
            <div className="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-900 dark:text-green-300">{overview.active_assets}</div>
              <div className="text-sm text-green-700 dark:text-green-400">Активных</div>
            </div>
            <div className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
              <div className="text-2xl font-bold text-yellow-900 dark:text-yellow-300">{overview.maintenance}</div>
              <div className="text-sm text-yellow-700 dark:text-yellow-400">На ремонте</div>
            </div>
            <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="text-2xl font-bold text-red-900 dark:text-red-300">{overview.written_off}</div>
              <div className="text-sm text-red-700 dark:text-red-400">Списано</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="text-sm text-gray-500 dark:text-gray-400">Общая стоимость</div>
              <div className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {overview.total_value?.toLocaleString('ru-RU')} ₽
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="text-sm text-gray-500 dark:text-gray-400">Суммарная амортизация</div>
              <div className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {overview.depreciation?.toLocaleString('ru-RU')} ₽
              </div>
            </div>
          </div>
        </>
      )}

      <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 dark:text-blue-300 mb-2">ℹ️ Доступная аналитика</h3>
        <ul className="text-sm text-blue-800 dark:text-blue-400 space-y-1 list-disc list-inside">
          <li>Тренды поломок: /api/analytics/breakdown-trends</li>
          <li>Расхождения: /api/analytics/discrepancies</li>
          <li>Рекомендации по закупкам: /api/analytics/purchase-recommendations</li>
          <li>Амортизация: /api/analytics/depreciation</li>
        </ul>
      </div>
    </div>
  );
};

export default AnalyticsPage;
