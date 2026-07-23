// frontend/src/pages/Dashboard.tsx
import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';

interface Stats {
  total: number;
  active: number;
  maintenance: number;
  written_off: number;
}

const Dashboard: React.FC = () => {
  const { isAuthenticated, isAdmin, user } = useAuth();
  const [dbStatus, setDbStatus] = useState<string>('checking...');
  const [dbDetails, setDbDetails] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [stats] = useState<Stats>({
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
        
        console.log('📡 Запрос к /api/db-check...');
        const response = await fetch('/api/db-check');
        
        console.log('📥 Ответ:', response);
        console.log('📥 Данные:', response.data);
        
        // Проверяем статус
        if (response.ok) {
          const data = await response.json();
          if (data && data.status === 'connected') {
            setDbStatus('connected');
            setDbDetails(data.database || 'papiBD');
          } else {
            setDbStatus('disconnected');
            setDbDetails(data?.error || 'Неизвестная ошибка');
          }
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { label: 'Всего активов', value: stats.total, color: 'blue' },
            { label: 'Активных', value: stats.active, color: 'green' },
            { label: 'На ремонте', value: stats.maintenance, color: 'yellow' },
            { label: 'Списано', value: stats.written_off, color: 'red' },
          ].map((stat) => (
            <div key={stat.label} className="bg-white rounded-lg shadow p-6">
              <div className="text-gray-500 text-sm">{stat.label}</div>
              <div className={`text-3xl font-bold text-${stat.color}-600`}>
                {stat.value}
              </div>
            </div>
          ))}
        </div>
      )}
      
      {isAdmin && (
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="text-lg font-medium text-blue-900 mb-2">Админ-панель</h3>
          <p className="text-sm text-blue-700 mb-3">
            У вас есть доступ к управлению пользователями системы.
          </p>
          <a href="/admin" className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            Перейти в админку
          </a>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
