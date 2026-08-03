import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useRepairs } from '../hooks/useRepairs';
import { useAuth } from '../hooks/useAuth';
import { UserRole } from '../domain/roles';

const RepairList: React.FC = () => {
  const { repairs, loading, error, deleteRepair } = useRepairs();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [searchTerm, setSearchTerm] = useState('');
  
  const filteredRepairs = repairs.filter((repair) =>
    repair.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    repair.asset_id.toString().includes(searchTerm)
  );

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
      rejected: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
      in_progress: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
      draft: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
    };
    return colors[status] || 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
  };

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      urgent: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
      high: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
      medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
    };
    return colors[priority] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  };

  const getStatusLabel = (status: string) => {
    const statusMap: Record<string, string> = {
      draft: 'Черновик',
      submitted: 'Подана',
      approved: 'Одобрена',
      in_progress: 'В работе',
      completed: 'Выполнена',
      rejected: 'Отклонена',
      cancelled: 'Отменена',
    };
    return statusMap[status] || status;
  };

  const getPriorityLabel = (priority: string) => {
    const priorityMap: Record<string, string> = {
      low: 'Низкий',
      medium: 'Средний',
      high: 'Высокий',
      urgent: 'Срочный',
    };
    return priorityMap[priority] || priority;
  };

  if (loading) return <div className="text-gray-500 dark:text-gray-400">Загрузка...</div>;
  if (error) return <div className="text-red-500 dark:text-red-400">Ошибка: {error}</div>;

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Заявки на ремонт</h1>
          <button
            onClick={() => navigate('/repairs/create')}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
          >
            Новая заявка
          </button>
        </div>
        <div className="relative">
          <input
            type="text"
            placeholder="Поиск по названию или ID актива..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md pl-10 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <div className="absolute left-3 top-2.5 text-gray-400 dark:text-gray-500">
            🔍
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 shadow border border-gray-100 dark:border-gray-700 overflow-hidden sm:rounded-lg">
        {filteredRepairs.length > 0 ? (
          <ul className="divide-y divide-gray-200 dark:divide-gray-700">
            {filteredRepairs.map((repair) => (
              <li key={repair.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50 dark:hover:bg-gray-750 transition">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-blue-600 dark:text-blue-400 truncate">
                      <Link to={`/repairs/${repair.id}`} className="hover:underline">
                        {repair.title}
                      </Link>
                    </p>
                    <div className="mt-1 flex items-center text-sm text-gray-500 dark:text-gray-400">
                      <span className="mr-2">Актив № {repair.asset_id}</span>
                      <span className="mx-2">•</span>
                      <span>Создано: {new Date(repair.created_at).toLocaleDateString('ru-RU')}</span>
                    </div>
                  </div>
                  <div className="ml-2 flex-shrink-0 flex space-x-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(repair.status)}`}>
                      {getStatusLabel(repair.status)}
                    </span>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(repair.priority)}`}>
                      {getPriorityLabel(repair.priority)}
                    </span>
                  </div>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    {repair.estimated_cost
                      ? new Intl.NumberFormat('ru-RU', {
                          style: 'currency',
                          currency: 'RUB',
                        }).format(Number(repair.estimated_cost))
                      : 'Цена не указана'}
                  </div>
                  {user?.role === UserRole.ADMIN && (
                    <div className="flex space-x-2">
                      <Link
                        to={`/repairs/${repair.id}/edit`}
                        className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300"
                      >
                        Редактировать
                      </Link>
                      <button
                        onClick={() => deleteRepair(repair.id)}
                        className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300"
                      >
                        Удалить
                      </button>
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="px-4 py-5 sm:p-6 text-center text-gray-500 dark:text-gray-400">
            Список заявок пуст
          </div>
        )}
      </div>
    </div>
  );
};

export default RepairList;
