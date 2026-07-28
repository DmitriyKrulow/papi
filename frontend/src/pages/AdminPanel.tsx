// frontend/src/pages/AdminPanel.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import type { Department, DepartmentOption, Employee, EmployeeOption } from '../types';

interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  phone?: string;
  role: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

interface UserFormData {
  username: string;
  email: string;
  full_name: string;
  phone: string;
  role: string;
  is_active: boolean;
}

interface PasswordResetData {
  password: string;
  confirmPassword: string;
}

interface DepartmentFormData {
  name: string;
  code: string;
  parent_id?: number;
  head: string;
  phone: string;
  email: string;
  location: string;
}

interface EmployeeFormData {
  first_name: string;
  last_name: string;
  middle_name: string;
  department_id: number;
  position: string;
  phone: string;
  email: string;
  employee_number: string;
}

const AdminPanel: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'users' | 'placements' | 'employees'>('users');
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingUser, setDeletingUser] = useState<number | null>(null);
  const [updatingRole, setUpdatingRole] = useState<number | null>(null);
  const [viewingUser, setViewingUser] = useState<User | null>(null);
  const [showUserForm, setShowUserForm] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [showPasswordReset, setShowPasswordReset] = useState(false);
  const [passwordResetData, setPasswordResetData] = useState<PasswordResetData>({
    password: '', confirmPassword: ''
  });
  const [userFormData, setUserFormData] = useState<UserFormData>({
    username: '', email: '', full_name: '', phone: '', role: 'user', is_active: false
  });
  const [resettingPassword, setResettingPassword] = useState<number | null>(null);

  // Placements state
  const [departments, setDepartments] = useState<Department[]>([]);
  const [deptLoading, setDeptLoading] = useState(false);
  const [deptSearch, setDeptSearch] = useState('');
  const [showDeptForm, setShowDeptForm] = useState(false);
  const [editingDept, setEditingDept] = useState<Department | null>(null);
  const [deptFormData, setDeptFormData] = useState<DepartmentFormData>({
    name: '', code: '', head: '', phone: '', email: '', location: ''
  });
  const [deptOptions, setDeptOptions] = useState<DepartmentOption[]>([]);

  // Employees state
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [empLoading, setEmpLoading] = useState(false);
  const [empSearch, setEmpSearch] = useState('');
  const [empDeptFilter, setEmpDeptFilter] = useState('');
  const [showEmpForm, setShowEmpForm] = useState(false);
  const [editingEmp, setEditingEmp] = useState<Employee | null>(null);
  const [empFormData, setEmpFormData] = useState<EmployeeFormData>({
    first_name: '', last_name: '', middle_name: '', department_id: 0, position: '', phone: '', email: '', employee_number: ''
  });
  const [empOptions, setEmpOptions] = useState<EmployeeOption[]>([]);

  useEffect(() => {
    fetchUsers();
  }, []);

  useEffect(() => {
    if (activeTab === 'placements') {
      fetchDepartments();
      fetchDeptOptions();
    }
    if (activeTab === 'employees') {
      fetchEmployees();
      fetchEmpOptions();
    }
  }, [activeTab]);

  const fetchDepartments = async () => {
    try {
      setDeptLoading(true);
      const token = localStorage.getItem('token');
      const params = deptSearch ? `?search=${encodeURIComponent(deptSearch)}` : '';
      const response = await fetch(`/api/admin/placements/${params}`, {
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      });
      if (response.ok) {
        const data = await response.json();
        setDepartments(data.items || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setDeptLoading(false);
    }
  };

  const fetchDeptOptions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/placements/options', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setDeptOptions(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchEmployees = async () => {
    try {
      setEmpLoading(true);
      const token = localStorage.getItem('token');
      let params = empSearch ? `?search=${encodeURIComponent(empSearch)}` : '';
      if (empDeptFilter) {
        params += (params ? '&' : '?') + `department_id=${empDeptFilter}`;
      }
      const response = await fetch(`/api/admin/employees/${params}`, {
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      });
      if (response.ok) {
        const data = await response.json();
        setEmployees(data.items || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setEmpLoading(false);
    }
  };

  const fetchEmpOptions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/employees/options', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setEmpOptions(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

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
          window.location.href = '/login';
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

  const handleViewUser = async (userId: number) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/users/${userId}`, {
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      });
      if (response.ok) {
        const user = await response.json();
        setViewingUser(user);
      }
    } catch (err) {
      console.error(err);
      toast.error('Ошибка загрузки данных пользователя');
    }
  };

  const handleEditUser = async () => {
    if (!userFormData.username || !userFormData.email) {
      toast.error('Имя пользователя и email обязательны');
      return;
    }
    try {
      const token = localStorage.getItem('token');
      const url = editingUser ? `/api/admin/users/${editingUser.id}` : `/api/admin/users`;
      const method = editingUser ? 'PUT' : 'POST';
      const response = await fetch(url, {
        method,
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(userFormData),
      });
      if (response.ok) {
        toast.success('Пользователь обновлен');
        setShowUserForm(false);
        setEditingUser(null);
        fetchUsers();
      } else {
        const data = await response.json();
        toast.error(data.detail || 'Ошибка обновления');
      }
    } catch (err) {
      toast.error('Ошибка обновления пользователя');
    }
  };

  const handlePasswordReset = async (userId: number) => {
    if (passwordResetData.password.length < 6) {
      toast.error('Пароль должен быть не менее 6 символов');
      return;
    }
    if (passwordResetData.password !== passwordResetData.confirmPassword) {
      toast.error('Пароли не совпадают');
      return;
    }
    try {
      setResettingPassword(userId);
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/users/${userId}/password`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: passwordResetData.password }),
      });
      if (response.ok) {
        toast.success('Пароль успешно сброшен');
        setShowPasswordReset(false);
        setPasswordResetData({ password: '', confirmPassword: '' });
      } else {
        const data = await response.json();
        toast.error(data.detail || 'Ошибка сброса пароля');
      }
    } catch (err) {
      toast.error('Ошибка сброса пароля');
    } finally {
      setResettingPassword(null);
    }
  };

  // Department handlers
  const handleCreateDepartment = async () => {
    if (!deptFormData.name || !deptFormData.code) {
      toast.error('Название и код обязательны');
      return;
    }
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/placements/', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(deptFormData),
      });
      if (response.ok) {
        toast.success('Подразделение создано');
        setShowDeptForm(false);
        setDeptFormData({ name: '', code: '', head: '', phone: '', email: '', location: '' });
        fetchDepartments();
      } else {
        const data = await response.json();
        toast.error(data.detail || 'Ошибка создания');
      }
    } catch (err) {
      toast.error('Ошибка создания подразделения');
    }
  };

  const handleUpdateDepartment = async () => {
    if (!editingDept) return;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/placements/${editingDept.id}/`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(deptFormData),
      });
      if (response.ok) {
        toast.success('Подразделение обновлено');
        setShowDeptForm(false);
        setEditingDept(null);
        fetchDepartments();
      } else {
        const data = await response.json();
        toast.error(data.detail || 'Ошибка обновления');
      }
    } catch (err) {
      toast.error('Ошибка обновления подразделения');
    }
  };

  const handleDeleteDepartment = async (id: number) => {
    if (!window.confirm('Удалить подразделение?')) return;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/placements/${id}/`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        toast.success('Подразделение удалено');
        fetchDepartments();
      } else {
        toast.error('Ошибка удаления');
      }
    } catch (err) {
      toast.error('Ошибка удаления подразделения');
    }
  };

  // Employee handlers
  const handleCreateEmployee = async () => {
    if (!empFormData.first_name || !empFormData.last_name || !empFormData.department_id) {
      toast.error('Имя, фамилия и подразделение обязательны');
      return;
    }
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/employees/', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(empFormData),
      });
      if (response.ok) {
        toast.success('Сотрудник создан');
        setShowEmpForm(false);
        setEmpFormData({ first_name: '', last_name: '', middle_name: '', department_id: 0, position: '', phone: '', email: '', employee_number: '' });
        fetchEmployees();
      } else {
        const data = await response.json();
        toast.error(data.detail || 'Ошибка создания');
      }
    } catch (err) {
      toast.error('Ошибка создания сотрудника');
    }
  };

  const handleUpdateEmployee = async () => {
    if (!editingEmp) return;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/employees/${editingEmp.id}/`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(empFormData),
      });
      if (response.ok) {
        toast.success('Сотрудник обновлен');
        setShowEmpForm(false);
        setEditingEmp(null);
        fetchEmployees();
      } else {
        const data = await response.json();
        toast.error(data.detail || 'Ошибка обновления');
      }
    } catch (err) {
      toast.error('Ошибка обновления сотрудника');
    }
  };

  const handleDeleteEmployee = async (id: number) => {
    if (!window.confirm('Удалить сотрудника?')) return;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/employees/${id}/`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        toast.success('Сотрудник удален');
        fetchEmployees();
      } else {
        toast.error('Ошибка удаления');
      }
    } catch (err) {
      toast.error('Ошибка удаления сотрудника');
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
                  onClick={() => window.location.href = '/dashboard'}
                className="text-blue-600 hover:text-blue-800 transition"
              >
                ← Назад в дашборд
              </button>
            </div>
            <p className="text-sm text-gray-500 mb-4">Управление системой</p>

            <div className="flex gap-1 mb-6 border-b">
              <button
                onClick={() => setActiveTab('users')}
                className={`px-4 py-2 font-medium text-sm rounded-t-lg transition ${activeTab === 'users' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
              >
                👥 Пользователи
              </button>
              <button
                onClick={() => setActiveTab('placements')}
                className={`px-4 py-2 font-medium text-sm rounded-t-lg transition ${activeTab === 'placements' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
              >
                🏢 Размещения
              </button>
              <button
                onClick={() => setActiveTab('employees')}
                className={`px-4 py-2 font-medium text-sm rounded-t-lg transition ${activeTab === 'employees' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
              >
                👤 Сотрудники
              </button>
            </div>
            
            {error && activeTab === 'users' && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                ❌ {error}
              </div>
            )}

            {activeTab === 'users' && (
              <>
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
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                              <div className="flex justify-end gap-2">
                                <button onClick={() => handleViewUser(user.id)} className="text-blue-600 hover:text-blue-800" title="Просмотреть">👁️</button>
                                <button onClick={() => { setEditingUser(user); setUserFormData({ username: user.username, email: user.email, full_name: user.full_name || '', phone: user.phone || '', role: user.role, is_active: user.is_active }); setShowUserForm(true); setShowPasswordReset(false); }} className="text-green-600 hover:text-green-800" title="Редактировать">✏️</button>
                                <button onClick={() => { setEditingUser(user); setShowPasswordReset(true); setPasswordResetData({ password: '', confirmPassword: '' }); }} className="text-yellow-600 hover:text-yellow-800" title="Сменить пароль">🔑</button>
                                <button onClick={() => handleDeleteUser(user.id)} disabled={deletingUser === user.id} className="text-red-600 hover:text-red-900 disabled:opacity-50">{deletingUser === user.id ? '...' : '🗑️'}</button>
                              </div>
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
              </>
            )}

            {showUserForm && activeTab === 'users' && (
              <div className="bg-gray-50 border rounded-lg p-4 mb-4">
                <h3 className="font-medium text-gray-700 mb-3">{editingUser ? 'Редактировать пользователя' : 'Новый пользователь'}</h3>
                {!showPasswordReset && (
                  <>
                    <div className="grid grid-cols-2 gap-3">
                      <input type="text" placeholder="Имя пользователя *" value={userFormData.username} onChange={(e) => setUserFormData({...userFormData, username: e.target.value})} className="px-3 py-2 border rounded text-sm" />
                      <input type="email" placeholder="Email *" value={userFormData.email} onChange={(e) => setUserFormData({...userFormData, email: e.target.value})} className="px-3 py-2 border rounded text-sm" />
                      <input type="text" placeholder="ФИО" value={userFormData.full_name} onChange={(e) => setUserFormData({...userFormData, full_name: e.target.value})} className="px-3 py-2 border rounded text-sm" />
                      <input type="text" placeholder="Телефон" value={userFormData.phone} onChange={(e) => setUserFormData({...userFormData, phone: e.target.value})} className="px-3 py-2 border rounded text-sm" />
                      <select value={userFormData.role} onChange={(e) => setUserFormData({...userFormData, role: e.target.value})} className="px-3 py-2 border rounded text-sm">
                        <option value="user">Пользователь</option>
                        <option value="admin">Администратор</option>
                        <option value="viewer">Наблюдатель</option>
                      </select>
                      <label className="flex items-center gap-2 text-sm">
                        <input type="checkbox" checked={userFormData.is_active} onChange={(e) => setUserFormData({...userFormData, is_active: e.target.checked})} className="rounded" />
                        {userFormData.is_active ? '✅ Активен' : '❌ Неактивен'}
                      </label>
                    </div>
                    <div className="flex gap-2 mt-3">
                      <button onClick={handleEditUser} className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 transition">Сохранить</button>
                      <button onClick={() => { setShowUserForm(false); setEditingUser(null); }} className="bg-gray-300 text-gray-700 px-4 py-1.5 rounded text-sm hover:bg-gray-400 transition">Отмена</button>
                    </div>
                  </>
                )}
              </div>
            )}

            {showPasswordReset && editingUser && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                <h3 className="font-medium text-yellow-900 mb-3">🔑 Сброс пароля для {editingUser.username}</h3>
                <div className="grid grid-cols-2 gap-3">
                  <input type="password" placeholder="Новый пароль (мин. 6 символов)" value={passwordResetData.password} onChange={(e) => setPasswordResetData({...passwordResetData, password: e.target.value})} className="px-3 py-2 border rounded text-sm" />
                  <input type="password" placeholder="Подтвердите пароль" value={passwordResetData.confirmPassword} onChange={(e) => setPasswordResetData({...passwordResetData, confirmPassword: e.target.value})} className="px-3 py-2 border rounded text-sm" />
                </div>
                <div className="flex gap-2 mt-3">
                  <button onClick={() => handlePasswordReset(editingUser.id)} disabled={resettingPassword === editingUser.id} className="bg-yellow-600 text-white px-4 py-1.5 rounded text-sm hover:bg-yellow-700 transition disabled:opacity-50">{resettingPassword === editingUser.id ? '...' : 'Сбросить пароль'}</button>
                  <button onClick={() => setShowPasswordReset(false)} className="bg-gray-300 text-gray-700 px-4 py-1.5 rounded text-sm hover:bg-gray-400 transition">Отмена</button>
                </div>
              </div>
            )}

            {viewingUser && (
              <div className="bg-gray-50 border rounded-lg p-4 mb-4">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="font-medium text-gray-700">👤 Информация о пользователе</h3>
                  <button onClick={() => setViewingUser(null)} className="text-gray-500 hover:text-gray-700 text-xl">&times;</button>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-xs text-gray-500">ID</span>
                    <p className="text-sm font-medium">{viewingUser.id}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">Имя пользователя</span>
                    <p className="text-sm font-medium">{viewingUser.username}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">Email</span>
                    <p className="text-sm font-medium">{viewingUser.email}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">ФИО</span>
                    <p className="text-sm font-medium">{viewingUser.full_name || '—'}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">Телефон</span>
                    <p className="text-sm font-medium">{viewingUser.phone || '—'}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">Роль</span>
                    <p className="text-sm font-medium">{viewingUser.role === 'admin' ? 'Администратор' : viewingUser.role === 'viewer' ? 'Наблюдатель' : 'Пользователь'}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">Статус</span>
                    <p className="text-sm font-medium">
                      <span className={`px-2 py-0.5 text-xs rounded-full ${viewingUser.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {viewingUser.is_active ? 'Активен' : 'Неактивен'}
                      </span>
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">Дата регистрации</span>
                    <p className="text-sm font-medium">{viewingUser.created_at ? new Date(viewingUser.created_at).toLocaleDateString('ru-RU') : '—'}</p>
                  </div>
                </div>
                <div className="flex gap-2 mt-4">
                  <button onClick={() => { setViewingUser(null); setEditingUser(viewingUser); setUserFormData({ username: viewingUser.username, email: viewingUser.email, full_name: viewingUser.full_name || '', phone: viewingUser.phone || '', role: viewingUser.role, is_active: viewingUser.is_active }); setShowUserForm(true); setShowPasswordReset(false); }} className="bg-green-600 text-white px-3 py-1.5 rounded text-sm hover:bg-green-700 transition">✏️ Редактировать</button>
                  <button onClick={() => { setViewingUser(null); setEditingUser(viewingUser); setShowPasswordReset(true); setPasswordResetData({ password: '', confirmPassword: '' }); }} className="bg-yellow-600 text-white px-3 py-1.5 rounded text-sm hover:bg-yellow-700 transition">🔑 Сменить пароль</button>
                </div>
              </div>
            )}

            {activeTab === 'placements' && (
              <>
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-semibold text-gray-800">Подразделения и размещения</h2>
                  <button
                    onClick={() => { setShowDeptForm(true); setEditingDept(null); setDeptFormData({ name: '', code: '', head: '', phone: '', email: '', location: '' }); }}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition text-sm"
                  >
                    ➕ Добавить подразделение
                  </button>
                </div>

                {showDeptForm && (
                  <div className="bg-gray-50 border rounded-lg p-4 mb-4">
                    <h3 className="font-medium text-gray-700 mb-3">{editingDept ? 'Редактировать подразделение' : 'Новое подразделение'}</h3>
                    <div className="grid grid-cols-2 gap-3">
                      <input type="text" placeholder="Название *" value={deptFormData.name} onChange={(e) => setDeptFormData({...deptFormData, name: e.target.value})} className="px-3 py-2 border rounded text-sm" />
                      <input type="text" placeholder="Код *" value={deptFormData.code} onChange={(e) => setDeptFormData({...deptFormData, code: e.target.value})} className="px-3 py-2 border rounded text-sm" />
                      <input type="text" placeholder="Руководитель" value={deptFormData.head} onChange={(e) => setDeptFormData({...deptFormData, head: e.target.value})} className="px-3 py-2 border rounded text-sm" />
                      <input type="text" placeholder="Телефон" value={deptFormData.phone} onChange={(e) => setDeptFormData({...deptFormData, phone: e.target.value})} className="px-3 py-2 border rounded text-sm" />
                      <input type="email" placeholder="Email" value={deptFormData.email} onChange={(e) => setDeptFormData({...deptFormData, email: e.target.value})} className="px-3 py-2 border rounded text-sm" />
                      <input type="text" placeholder="Местоположение" value={deptFormData.location} onChange={(e) => setDeptFormData({...deptFormData, location: e.target.value})} className="px-3 py-2 border rounded text-sm" />
                    </div>
                    <div className="flex gap-2 mt-3">
                      <button onClick={editingDept ? handleUpdateDepartment : handleCreateDepartment} className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 transition">{editingDept ? 'Сохранить' : 'Создать'}</button>
                      <button onClick={() => { setShowDeptForm(false); setEditingDept(null); }} className="bg-gray-300 text-gray-700 px-4 py-1.5 rounded text-sm hover:bg-gray-400 transition">Отмена</button>
                    </div>
                  </div>
                )}

                <div className="mb-4">
                  <input
                    type="text"
                    placeholder="Поиск подразделений..."
                    value={deptSearch}
                    onChange={(e) => { setDeptSearch(e.target.value); }}
                    className="px-4 py-2 border border-gray-300 rounded-lg w-full text-sm"
                  />
                </div>

                {deptLoading ? (
                  <div className="text-center py-8 text-gray-500">Загрузка...</div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Код</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Название</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Руководитель</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Местоположение</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Действия</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {departments.length === 0 ? (
                          <tr><td colSpan={5} className="px-4 py-4 text-center text-gray-500 text-sm">Нет подразделений</td></tr>
                        ) : (
                          departments.map((dept) => (
                            <tr key={dept.id} className="hover:bg-gray-50">
                              <td className="px-4 py-2 text-sm font-mono text-gray-900">{dept.code}</td>
                              <td className="px-4 py-2 text-sm text-gray-900">{dept.name}</td>
                              <td className="px-4 py-2 text-sm text-gray-600">{dept.head || '—'}</td>
                              <td className="px-4 py-2 text-sm text-gray-600">{dept.location || '—'}</td>
                              <td className="px-4 py-2 text-right text-sm">
                                <button onClick={() => { setEditingDept(dept); setDeptFormData({ name: dept.name, code: dept.code, head: dept.head || '', phone: dept.phone || '', email: dept.email || '', location: dept.location || '' }); setShowDeptForm(true); }} className="text-blue-600 hover:text-blue-800 mr-3">✏️</button>
                                <button onClick={() => handleDeleteDepartment(dept.id)} className="text-red-600 hover:text-red-900">🗑️</button>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                )}

                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h3 className="text-sm font-medium text-blue-900 mb-2">📋 Управление размещениями</h3>
                  <p className="text-xs text-blue-700 mb-2">На странице активов используйте фильтры по подразделению и сотруднику для поиска. Для назначения актива используйте редактирование актива.</p>
                  <p className="text-xs text-blue-700">Сотрудники, связанные с подразделением, автоматически отображаются при выборе этого подразделения.</p>
                </div>
              </>
            )}

            {activeTab === 'employees' && (
              <>
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-semibold text-gray-800">Сотрудники</h2>
                  <button
                    onClick={() => { setShowEmpForm(true); setEditingEmp(null); setEmpFormData({ first_name: '', last_name: '', middle_name: '', department_id: 0, position: '', phone: '', email: '', employee_number: '' }); }}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition text-sm"
                  >
                    ➕ Добавить сотрудника
                  </button>
                </div>

                {showEmpForm && (
                  <div className="bg-gray-50 border rounded-lg p-4 mb-4">
                    <h3 className="font-medium text-gray-700 mb-3">{editingEmp ? 'Редактировать сотрудника' : 'Новый сотрудник'}</h3>
                    <div className="grid grid-cols-2 gap-3">
                      <input type="text" placeholder="Фамилия *" value={empFormData.last_name} onChange={(e) => setEmpFormData({...empFormData, last_name: e.target.value})} className="px-3 py-2 border rounded text-sm" />
                      <input type="text" placeholder="Имя *" value={empFormData.first_name} onChange={(e) => setEmpFormData({...empFormData, first_name: e.target.value})} className="px-3 py-2 border rounded text-sm" />
                      <input type="text" placeholder="Отчество" value={empFormData.middle_name} onChange={(e) => setEmpFormData({...empFormData, middle_name: e.target.value})} className="px-3 py-2 border rounded text-sm" />
                      <select value={empFormData.department_id} onChange={(e) => setEmpFormData({...empFormData, department_id: Number(e.target.value)})} className="px-3 py-2 border rounded text-sm">
                        <option value={0}>Выберите подразделение</option>
                        {departments.map(d => <option key={d.id} value={d.id}>{d.name} ({d.code})</option>)}
                      </select>
                      <input type="text" placeholder="Должность" value={empFormData.position} onChange={(e) => setEmpFormData({...empFormData, position: e.target.value})} className="px-3 py-2 border rounded text-sm" />
                      <input type="text" placeholder="Телефон" value={empFormData.phone} onChange={(e) => setEmpFormData({...empFormData, phone: e.target.value})} className="px-3 py-2 border rounded text-sm" />
                      <input type="email" placeholder="Email" value={empFormData.email} onChange={(e) => setEmpFormData({...empFormData, email: e.target.value})} className="px-3 py-2 border rounded text-sm" />
                      <input type="text" placeholder="Табельный номер" value={empFormData.employee_number} onChange={(e) => setEmpFormData({...empFormData, employee_number: e.target.value})} className="px-3 py-2 border rounded text-sm" />
                    </div>
                    <div className="flex gap-2 mt-3">
                      <button onClick={editingEmp ? handleUpdateEmployee : handleCreateEmployee} className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 transition">{editingEmp ? 'Сохранить' : 'Создать'}</button>
                      <button onClick={() => { setShowEmpForm(false); setEditingEmp(null); }} className="bg-gray-300 text-gray-700 px-4 py-1.5 rounded text-sm hover:bg-gray-400 transition">Отмена</button>
                    </div>
                  </div>
                )}

                <div className="flex gap-3 mb-4">
                  <input
                    type="text"
                    placeholder="Поиск сотрудников..."
                    value={empSearch}
                    onChange={(e) => setEmpSearch(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg flex-1 text-sm"
                  />
                  <select
                    value={empDeptFilter}
                    onChange={(e) => setEmpDeptFilter(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="">Все подразделения</option>
                    {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </select>
                </div>

                {empLoading ? (
                  <div className="text-center py-8 text-gray-500">Загрузка...</div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">ФИО</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Должность</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Подразделение</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Телефон</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Действия</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {employees.length === 0 ? (
                          <tr><td colSpan={6} className="px-4 py-4 text-center text-gray-500 text-sm">Нет сотрудников</td></tr>
                        ) : (
                          employees.map((emp) => (
                            <tr key={emp.id} className="hover:bg-gray-50">
                              <td className="px-4 py-2 text-sm text-gray-900">{emp.first_name} {emp.last_name}{emp.middle_name ? ` ${emp.middle_name}` : ''}</td>
                              <td className="px-4 py-2 text-sm text-gray-600">{emp.position || '—'}</td>
                              <td className="px-4 py-2 text-sm text-gray-600">{emp.department_name || emp.department_code || '—'}</td>
                              <td className="px-4 py-2 text-sm text-gray-600">{emp.phone || '—'}</td>
                              <td className="px-4 py-2 text-sm text-gray-600">{emp.email || '—'}</td>
                              <td className="px-4 py-2 text-right text-sm">
                                <button onClick={() => { setEditingEmp(emp); setEmpFormData({ first_name: emp.first_name, last_name: emp.last_name, middle_name: emp.middle_name || '', department_id: emp.department_id || 0, position: emp.position || '', phone: emp.phone || '', email: emp.email || '', employee_number: emp.employee_number || '' }); setShowEmpForm(true); }} className="text-blue-600 hover:text-blue-800 mr-3">✏️</button>
                                <button onClick={() => handleDeleteEmployee(emp.id)} className="text-red-600 hover:text-red-900">🗑️</button>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                )}

                <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <h3 className="text-sm font-medium text-green-900 mb-2">👤 Сотрудники и активы</h3>
                  <p className="text-xs text-green-700">Сотрудники могут быть назначены ответственными за активы. При назначении актива сотруднику его ФИО автоматически подтягивается из списка сотрудников подразделения.</p>
                </div>
              </>
            )}

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-lg font-medium text-blue-900 mb-2">ℹ️ Информация</h3>
              <ul className="list-disc list-inside text-sm text-blue-700 space-y-1">
                <li>Здесь вы можете управлять пользователями, подразделениями и сотрудниками</li>
                <li>Подразделения используются для размещения активов</li>
                <li>Сотрудники могут быть назначены ответственными за активы</li>
                <li>Начальный администратор: <strong>admin</strong> (пароль: <strong>admin123</strong>)</li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AdminPanel;
