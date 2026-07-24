// frontend/src/pages/Dashboard.tsx
import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
// Удаляем неиспользуемые импорты
// import { apiClient } from '../api/client';
// import toast from 'react-hot-toast';

interface Stats {
  total: number;
  active: number;
  maintenance: number;
  written_off: number;
}

const Dashboard: React.FC = () => {
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

  useEffect(() => {
    if (!isAuthenticated) {
      window.location.href = '/login';
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Проверка БД
        console.log('📡 Запрос к /api/db-check...');
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
        
        // Получение статистики с бэкенда
        console.log('📡 Запрос к /api/reports/inventory-report...');
        const statsResponse = await fetch('/api/reports/inventory-report', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (statsResponse.ok) {
          const statsData = await statsResponse.json();
          console.log('📥 Статистика:', statsData);
          
          if (statsData.stats) {
            setStats({
              total: statsData.stats.total || 0,
              active: statsData.stats.active || 0,
              maintenance: statsData.stats.maintenance || 0,
              written_off: statsData.stats.written_off || 0,
            });
          }
        } else {
          console.warn('Не удалось загрузить статистику:', statsResponse.status);
        }
        
        setLoading(false);
      } catch (err: any) {
        console.error('❌ Ошибка:', err);
        setDbStatus('disconnected');
        setDbDetails(err.message || 'Ошибка соединения');
        setLoading(false);
      }
    };
    
    fetchData();
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900">Загрузка...</h2>
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
    blue: 'text-blue-600',
    green: 'text-green-600',
    yellow: 'text-yellow-600',
    red: 'text-red-600',
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">
        📊 Дашборд
      </h1>

      <div className="mb-6 p-4 bg-white rounded-lg shadow">
        <div className="flex items-center space-x-2">
          <span className="font-medium">Статус БД:</span>
          <span
            className={`px-3 py-1 rounded-full text-sm font-medium ${
              dbStatus === 'connected'
                ? 'bg-green-100 text-green-700'
                : dbStatus === 'checking...'
                ? 'bg-yellow-100 text-yellow-700'
                : 'bg-red-100 text-red-700'
            }`}
          >
            {dbStatus === 'connected' ? '✅ Подключена' :
             dbStatus === 'checking...' ? '⏳ Проверка...' :
             '❌ Отключена'}
          </span>
          {dbDetails && (
            <span className="text-sm text-gray-500 ml-2">
              ({dbDetails})
            </span>
          )}
        </div>
        {error && (
          <div className="mt-2 text-sm text-red-600">
            Ошибка: {error}
          </div>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center items-center py-12">
          <div className="text-gray-500">Загрузка данных...</div>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {statCards.map((stat) => (
              <div key={stat.label} className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-2xl">{stat.icon}</div>
                  <div className={`text-2xl font-bold ${colorClasses[stat.color as keyof typeof colorClasses]}`}>
                    {stat.value}
                  </div>
                </div>
                <div className="text-gray-500 text-sm">{stat.label}</div>
              </div>
            ))}
          </div>

          {/* Дополнительная информация */}
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">📈 Общая статистика</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center border-b pb-2">
                  <span className="text-gray-600">Всего активов:</span>
                  <span className="font-bold text-blue-600">{stats.total}</span>
                </div>
                <div className="flex justify-between items-center border-b pb-2">
                  <span className="text-gray-600">Активных:</span>
                  <span className="font-bold text-green-600">{stats.active}</span>
                </div>
                <div className="flex justify-between items-center border-b pb-2">
                  <span className="text-gray-600">На ремонте:</span>
                  <span className="font-bold text-yellow-600">{stats.maintenance}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Списано:</span>
                  <span className="font-bold text-red-600">{stats.written_off}</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">🔍 Быстрый доступ</h3>
              <div className="space-y-3">
                <button
                  onClick={() => window.location.href = '/assets'}
                  className="w-full text-left px-4 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition"
                >
                  📦 Перейти к активам
                </button>
                <button
                  onClick={() => window.location.href = '/reports'}
                  className="w-full text-left px-4 py-2 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition"
                >
                  📊 Перейти к отчетам
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Dashboard;