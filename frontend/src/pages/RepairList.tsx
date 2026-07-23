import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useRepairs } from '../hooks/useRepairs';
import { useAuth } from '../hooks/useAuth';
import { UserRole } from '../domain/roles';

const RepairList: React.FC = () => {
  const { repairs, loading, error, deleteRepair } = useRepairs();
  const { user } = useAuth();
  const navigate = useNavigate();

  const filteredRepairs = repairs.filter((repair) =>
    repair.title.toLowerCase().includes('') ||
    repair.asset_id.toString().includes('')
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) return <div>Загрузка...</div>;
  if (error) return <div className="text-red-500">Ошибка: {error}</div>;

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Заявки на ремонт</h1>
        <button
          onClick={() => navigate('/repairs/create')}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Новая заявка
        </button>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        {filteredRepairs.length > 0 ? (
          <ul className="divide-y divide-gray-200">
            {filteredRepairs.map((repair) => (
              <li key={repair.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-blue-600 truncate">
                      <Link to={`/repairs/${repair.id}`} className="hover:underline">
                        {repair.title}
                      </Link>
                    </p>
                    <div className="mt-1 flex items-center text-sm text-gray-500">
                      <span className="mr-2">Актив № {repair.asset_id}</span>
                      <span className="mx-2">•</span>
                      <span>Создано: {new Date(repair.created_at).toLocaleDateString('ru-RU')}</span>
                    </div>
                  </div>
                  <div className="ml-2 flex-shrink-0 flex space-x-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(repair.status)}`}>
                      {repair.status}
                    </span>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(repair.priority)}`}>
                      {repair.priority}
                    </span>
                  </div>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <div className="text-sm text-gray-500">
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
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Редактировать
                      </Link>
                      <button
                        onClick={() => deleteRepair(repair.id)}
                        className="text-red-600 hover:text-red-900"
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
          <div className="px-4 py-5 sm:p-6 text-center text-gray-500">
            Список заявок пуст
          </div>
        )}
      </div>
    </div>
  );
};

export default RepairList;
