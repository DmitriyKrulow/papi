// frontend/src/pages/AdminPanel.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  phone?: string;
  role: string;
  is_active: boolean;
  created_at?: string;
}

const AdminPanel: React.FC = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingUser, setDeletingUser] = useState<number | null>(null);
  const [updatingRole, setUpdatingRole] = useState<number | null>(null);

  // Проверяем авторизацию и права администратора
  useEffect(() => {
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');
    
    if (!token) {
      navigate('/login');
      return;
    }

    // Проверяем роль
    try {
      const user = userStr ? JSON.parse(userStr) : null;
      if (user?.role !== 'admin') {
        toast.error('Доступ запрещен. Требуются права администратора.');
        navigate('/dashboard');
        return;
      }
    } catch {
      navigate('/dashboard');
      return;
    }

    fetchUsers();
  }, [navigate]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/users', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          navigate('/login');
          return;
        }
        throw new Error(`Failed to fetch users: ${response.status}`);
      }

      const data = await response.json();
      setUsers(Array.isArray(data) ? data : data.items || []);
      setError(null);
    } catch (err) {
      setError('Ошибка при загрузке пользователей');
      console.error(err);
      toast.error('Ошибка загрузки пользователей');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!window.confirm('Вы уверены, что хотите удалить этого пользователя?')) {
      return;
    }

    try {
      setDeletingUser(userId);
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete user');
      }

      setUsers(users.filter(u => u.id !== userId));
      toast.success('Пользователь удален');
    } catch (err) {
      setError('Ошибка при удалении пользователя');
      console.error(err);
      toast.error('Ошибка удаления пользователя');
    } finally {
      setDeletingUser(null);
    }
  };

  const handleRoleChange = async (userId: number, newRole: string) => {
    try {
      setUpdatingRole(userId);
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/users/${userId}/role`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ role: newRole }),
      });

      if (!response.ok) {
        throw new Error('Failed to update role');
      }

      setUsers(users.map(u => 
        u.id === userId ? { ...u, role: newRole } : u
      ));
      toast.success('Роль обновлена');
    } catch (err) {
      setError('Ошибка при изменении роли');
      console.error(err);
      toast.error('Ошибка изменения роли');
    } finally {
      setUpdatingRole(null);
    }
  };

  if (loading && users.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">Загрузка...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <main className="flex-grow container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="bg-white shadow rounded-lg p-6 mb-6">
            <div className="flex justify-between items-center mb-4">
              <h1 className="text-2xl font-bold text-gray-900">👑 Админ-панель</h1>
              <button
                onClick={() => navigate('/dashboard')}
                className="text-blue-600 hover:text-blue-800 transition"
              >
                ← Назад в дашборд
              </button>
            </div>
            <p className="text-sm text-gray-500 mb-4">Управление пользователями системы</p>
            
            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                ❌ {error}
              </div>
            )}

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Имя пользователя</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ФИО</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Роль</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Статус</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Действия</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {users.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                        Пользователей пока нет
                      </td>
                    </tr>
                  ) : (
                    users.map((user) => (
                      <tr key={user.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{user.id}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{user.username}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{user.email}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {user.full_name || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <select
                            value={user.role}
                            onChange={(e) => handleRoleChange(user.id, e.target.value)}
                            disabled={updatingRole === user.id}
                            className="px-2 py-1 border rounded-md text-sm disabled:opacity-50"
                          >
                            <option value="user">Пользователь</option>
                            <option value="admin">Администратор</option>
                            <option value="viewer">Наблюдатель</option>
                          </select>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs rounded-full ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                            {user.is_active ? 'Активен' : 'Неактивен'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button
                            onClick={() => handleDeleteUser(user.id)}
                            disabled={deletingUser === user.id}
                            className="text-red-600 hover:text-red-900 disabled:opacity-50"
                          >
                            {deletingUser === user.id ? 'Удаление...' : '🗑️ Удалить'}
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {users.length > 0 && (
              <div className="mt-4 text-sm text-gray-500">
                Всего пользователей: {users.length}
              </div>
            )}
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-lg font-medium text-blue-900 mb-2">ℹ️ Информация</h3>
            <ul className="list-disc list-inside text-sm text-blue-700 space-y-1">
              <li>Здесь вы можете управлять всеми пользователями системы</li>
              <li>Администраторы имеют полный доступ ко всем функциям</li>
              <li>Обычные пользователи могут управлять только своими данными</li>
              <li>Начальный администратор: <strong>admin</strong> (пароль: <strong>admin123</strong>)</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AdminPanel;