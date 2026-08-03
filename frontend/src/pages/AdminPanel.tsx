// frontend/src/pages/AdminPanel.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import type { Department, Employee } from '../types';

interface TreeDepartment {
  id: number;
  name: string;
  code: string;
  parent_id?: number;
  head?: string;
  phone?: string;
  email?: string;
  location?: string;
  is_active: boolean;
  rooms: TreeRoom[];
}

interface TreeRoom {
  id: number;
  name: string;
  floor?: string;
  building?: string;
}

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

interface PasswordResetRequest {
  id: number;
  user_id: number;
  username: string;
  email: string;
  full_name?: string;
  reason: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  admin_comment?: string;
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

interface RoomFormData {
  name: string;
  floor: string;
  building: string;
}

const AdminPanel: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'users' | 'placements' | 'employees' | 'password-requests'>('users');
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
  const [deptTree, setDeptTree] = useState<TreeDepartment[]>([]);
  const [deptLoading, setDeptLoading] = useState(false);
  const [deptSearch, setDeptSearch] = useState('');
  const [showDeptForm, setShowDeptForm] = useState(false);
  const [editingDept, setEditingDept] = useState<Department | null>(null);
  const [deptFormData, setDeptFormData] = useState<DepartmentFormData>({
    name: '', code: '', head: '', phone: '', email: '', location: ''
  });
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [empLoading, setEmpLoading] = useState(false);
  const [empSearch, setEmpSearch] = useState('');
  const [empDeptFilter, setEmpDeptFilter] = useState('');
  const [showEmpForm, setShowEmpForm] = useState(false);
  const [editingEmp, setEditingEmp] = useState<Employee | null>(null);
  const [empFormData, setEmpFormData] = useState<EmployeeFormData>({
    first_name: '', last_name: '', middle_name: '', department_id: 0, position: '', phone: '', email: '', employee_number: ''
  });

  // Rooms state
  const [expandedDepts, setExpandedDepts] = useState<Set<number>>(new Set());
  const [showRoomForm, setShowRoomForm] = useState(false);
  const [editingRoom, setEditingRoom] = useState<TreeRoom | null>(null);
  const [roomFormData, setRoomFormData] = useState<RoomFormData>({
    name: '', floor: '', building: ''
  });
  const [roomDeptId, setRoomDeptId] = useState<number | null>(null);

  // Password reset requests state
  const [passwordRequests, setPasswordRequests] = useState<PasswordResetRequest[]>([]);
  const [requestsLoading, setRequestsLoading] = useState(false);
  const [requestsFilter, setRequestsFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('all');

  useEffect(() => {
    fetchUsers();
  }, []);

  useEffect(() => {
    if (activeTab === 'placements' || activeTab === 'employees') {
      fetchDepartments();
      fetchDeptOptions();
    }
    if (activeTab === 'employees') {
      fetchEmployees();
      fetchEmpOptions();
    }
    if (activeTab === 'password-requests') {
      fetchPasswordRequests();
    }
  }, [activeTab]);

  const fetchDepartments = async () => {
    try {
      setDeptLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/placements/tree', {
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      });
      if (response.ok) {
        const data = await response.json();
        setDeptTree(data);
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
        console.log('Dept options loaded:', data.length);
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
        console.log('Emp options loaded:', data.length);
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

  // Password reset request handlers
  const fetchPasswordRequests = async () => {
    try {
      setRequestsLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/password-reset/requests', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setPasswordRequests(Array.isArray(data) ? data : data.items || []);
      }
    } catch (err) {
      console.error('Failed to fetch password requests:', err);
    } finally {
      setRequestsLoading(false);
    }
  };

  const handlePasswordRequestAction = async (requestId: number, action: 'approve' | 'reject') => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/password-reset/requests/${requestId}/${action}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        toast.success(action === 'approve' ? 'Заявка одобрена, пароль отправлен пользователю' : 'Заявка отклонена');
        fetchPasswordRequests();
      } else {
        toast.error('Ошибка обработки заявки');
      }
    } catch (err) {
      toast.error('Ошибка обработки заявки');
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
      const response = await fetch('/api/admin/placements', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(deptFormData),
      });
      if (response.ok) {
        toast.success('Подразделение создано');
        setShowDeptForm(false);
        setDeptFormData({ name: '', code: '', head: '', phone: '', email: '', location: '' });
        await fetchDepartments();
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
        await fetchDepartments();
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
        await fetchDepartments();
      } else {
        toast.error('Ошибка удаления');
      }
    } catch (err) {
      toast.error('Ошибка удаления подразделения');
    }
  };

  // Room handlers
  const toggleDeptRooms = async (deptId: number) => {
    if (expandedDepts.has(deptId)) {
      setExpandedDepts(prev => {
        const next = new Set(prev);
        next.delete(deptId);
        return next;
      });
    } else {
      setExpandedDepts(prev => new Set([...prev, deptId]));
    }
  };

  const handleCreateRoom = async () => {
    if (!roomFormData.name || roomDeptId === null) {
      toast.error('Название обязательно и подразделение не выбрано');
      return;
    }
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/placements/${roomDeptId}/rooms`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(roomFormData),
      });
      if (response.ok) {
        toast.success('Кабинет добавлен');
        setShowRoomForm(false);
        setRoomFormData({ name: '', floor: '', building: '' });
        setRoomDeptId(null);
        setEditingRoom(null);
        await fetchDepartments();
      } else {
        const data = await response.json();
        toast.error(data.detail || 'Ошибка добавления');
      }
    } catch (err) {
      toast.error('Ошибка добавления кабинета');
    }
  };

  const handleUpdateRoom = async () => {
    if (!editingRoom || !roomFormData.name) return;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/placements/rooms/${editingRoom.id}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(roomFormData),
      });
      if (response.ok) {
        toast.success('Кабинет обновлен');
        setShowRoomForm(false);
        setEditingRoom(null);
        setRoomFormData({ name: '', floor: '', building: '' });
        await fetchDepartments();
      } else {
        const data = await response.json();
        toast.error(data.detail || 'Ошибка обновления');
      }
    } catch (err) {
      toast.error('Ошибка обновления кабинета');
    }
  };

  const handleDeleteRoom = async (roomId: number) => {
    if (!window.confirm('Удалить кабинет?')) return;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/placements/rooms/${roomId}/`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        toast.success('Кабинет удален');
        await fetchDepartments();
      } else {
        toast.error('Ошибка удаления');
      }
    } catch (err) {
      toast.error('Ошибка удаления кабинета');
    }
  };

  const findDeptInTree = (tree: TreeDepartment[], id: number): TreeDepartment | null => {
    for (const dept of tree) {
      if (dept.id === id) return dept;
      if (dept.rooms) {
        for (const room of dept.rooms) {
          if (room.id === id) return dept;
        }
      }
      const found = findDeptInTree(dept.rooms ? [] : [], id);
      if (found) return found;
    }
    return null;
  };

  const handleEditRoom = (dept: TreeDepartment, room: TreeRoom) => {
    setEditingRoom(room);
    setRoomFormData({ name: room.name, floor: room.floor || '', building: room.building || '' });
    setRoomDeptId(dept.id);
    setShowRoomForm(true);
  };

  // Employee handlers
  const handleCreateEmployee = async () => {
    if (!empFormData.first_name || !empFormData.last_name || !empFormData.department_id) {
      toast.error('Имя, фамилия и подразделение обязательны');
      return;
    }
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/employees', {
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

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      <main className="flex-grow container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6 border border-gray-100 dark:border-gray-700">
            {loading ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">Загрузка...</div>
            ) : (
              <>
                <div className="flex justify-between items-center mb-4">
                  <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">👑 Админ-панель</h1>
                    <button
                      onClick={() => navigate('/dashboard')}
                    className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition"
                  >
                    ← Назад в дашборд
                  </button>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">Управление системой</p>

                <div className="flex gap-1 mb-6 border-b border-gray-200 dark:border-gray-700">
                  <button
                    onClick={() => setActiveTab('users')}
                    className={`px-4 py-2 font-medium text-sm rounded-t-lg transition ${activeTab === 'users' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'}`}
                  >
                    👥 Пользователи
                  </button>
                  <button
                    onClick={() => setActiveTab('placements')}
                    className={`px-4 py-2 font-medium text-sm rounded-t-lg transition ${activeTab === 'placements' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'}`}
                  >
                    🏢 Размещения
                  </button>
                  <button
                    onClick={() => setActiveTab('employees')}
                    className={`px-4 py-2 font-medium text-sm rounded-t-lg transition ${activeTab === 'employees' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'}`}
                  >
                    👤 Сотрудники
                  </button>
                  <button
                    onClick={() => setActiveTab('password-requests')}
                    className={`px-4 py-2 font-medium text-sm rounded-t-lg transition ${activeTab === 'password-requests' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'}`}
                  >
                    🔑 Заявки на сброс пароля
                    {passwordRequests.filter(r => r.status === 'pending').length > 0 && (
                      <span className="ml-2 bg-red-500 text-white text-xs px-1.5 py-0.5 rounded-full">
                        {passwordRequests.filter(r => r.status === 'pending').length}
                      </span>
                    )}
                  </button>
                </div>
                
                {error && activeTab === 'users' && (
                  <div className="bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-300 px-4 py-3 rounded mb-4">
                    ❌ {error}
                  </div>
                )}

            {activeTab === 'users' && (
              <>
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Пользователи системы</h2>
                  <button
                    onClick={() => { setEditingUser(null); setUserFormData({ username: '', email: '', full_name: '', phone: '', role: 'user', is_active: true }); setShowUserForm(true); setShowPasswordReset(false); }}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition text-sm"
                  >
                    ➕ Создать пользователя
                  </button>
                </div>

                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">ID</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Имя пользователя</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Email</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">ФИО</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Роль</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Статус</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Действия</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                      {users.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="px-6 py-4 text-center text-gray-500 dark:text-gray-400">
                            Пользователей пока нет
                          </td>
                        </tr>
                      ) : (
                        users.map((user) => (
                          <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-750 transition">
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{user.id}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">{user.username}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{user.email}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                              {user.full_name || '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <select
                                value={user.role}
                                onChange={(e) => handleRoleChange(user.id, e.target.value)}
                                disabled={updatingRole === user.id}
                                className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 disabled:opacity-50"
                              >
                                <option value="user">Пользователь</option>
                                <option value="admin">Администратор</option>
                                <option value="responsible">Ответственный</option>
                              </select>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 text-xs rounded-full ${user.is_active ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'}`}>
                                {user.is_active ? 'Активен' : 'Неактивен'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                              <div className="flex justify-end gap-2">
                                <button onClick={() => handleViewUser(user.id)} className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300" title="Просмотреть">👁️</button>
                                <button onClick={() => { setEditingUser(user); setUserFormData({ username: user.username, email: user.email, full_name: user.full_name || '', phone: user.phone || '', role: user.role, is_active: user.is_active }); setShowUserForm(true); setShowPasswordReset(false); }} className="text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300" title="Редактировать">✏️</button>
                                <button onClick={() => { setEditingUser(user); setShowPasswordReset(true); setPasswordResetData({ password: '', confirmPassword: '' }); }} className="text-yellow-600 dark:text-yellow-400 hover:text-yellow-800 dark:hover:text-yellow-300" title="Сменить пароль">🔑</button>
                                <button onClick={() => handleDeleteUser(user.id)} disabled={deletingUser === user.id} className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300 disabled:opacity-50">{deletingUser === user.id ? '...' : '🗑️'}</button>
                              </div>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                {users.length > 0 && (
                  <div className="mt-4 text-sm text-gray-500 dark:text-gray-400">
                    Всего пользователей: {users.length}
                  </div>
                )}
              </>
            )}

            {showUserForm && activeTab === 'users' && (
              <div className="bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4 mb-4">
                <h3 className="font-medium text-gray-700 dark:text-gray-300 mb-3">{editingUser ? 'Редактировать пользователя' : 'Новый пользователь'}</h3>
                {!showPasswordReset && (
                  <>
                    <div className="grid grid-cols-2 gap-3">
                      <input type="text" placeholder="Имя пользователя *" value={userFormData.username} onChange={(e) => setUserFormData({...userFormData, username: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
                      <input type="email" placeholder="Email *" value={userFormData.email} onChange={(e) => setUserFormData({...userFormData, email: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
                      <input type="text" placeholder="ФИО" value={userFormData.full_name} onChange={(e) => setUserFormData({...userFormData, full_name: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
                      <input type="text" placeholder="Телефон" value={userFormData.phone} onChange={(e) => setUserFormData({...userFormData, phone: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
                      <select value={userFormData.role} onChange={(e) => setUserFormData({...userFormData, role: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                        <option value="user">Пользователь</option>
                        <option value="admin">Администратор</option>
                        <option value="responsible">Ответственный</option>
                      </select>
                      <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                        <input type="checkbox" checked={userFormData.is_active} onChange={(e) => setUserFormData({...userFormData, is_active: e.target.checked})} className="rounded" />
                        {userFormData.is_active ? '✅ Активен' : '❌ Неактивен'}
                      </label>
                    </div>
                    <div className="flex gap-2 mt-3">
                      <button onClick={handleEditUser} className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 transition">Сохранить</button>
                      <button onClick={() => { setShowUserForm(false); setEditingUser(null); }} className="bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-200 px-4 py-1.5 rounded text-sm hover:bg-gray-400 dark:hover:bg-gray-500 transition">Отмена</button>
                    </div>
                  </>
                )}
              </div>
            )}

            {showPasswordReset && editingUser && (
              <div className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-4">
                <h3 className="font-medium text-yellow-900 dark:text-yellow-300 mb-3">🔑 Сброс пароля для {editingUser.username}</h3>
                <div className="grid grid-cols-2 gap-3">
                  <input type="password" placeholder="Новый пароль (мин. 6 символов)" value={passwordResetData.password} onChange={(e) => setPasswordResetData({...passwordResetData, password: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
                  <input type="password" placeholder="Подтвердите пароль" value={passwordResetData.confirmPassword} onChange={(e) => setPasswordResetData({...passwordResetData, confirmPassword: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
                </div>
                <div className="flex gap-2 mt-3">
                  <button onClick={() => handlePasswordReset(editingUser.id)} disabled={resettingPassword === editingUser.id} className="bg-yellow-600 text-white px-4 py-1.5 rounded text-sm hover:bg-yellow-700 transition disabled:opacity-50">{resettingPassword === editingUser.id ? '...' : 'Сбросить пароль'}</button>
                  <button onClick={() => setShowPasswordReset(false)} className="bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-200 px-4 py-1.5 rounded text-sm hover:bg-gray-400 dark:hover:bg-gray-500 transition">Отмена</button>
                </div>
              </div>
            )}

            {viewingUser && (
              <div className="bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4 mb-4">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="font-medium text-gray-700 dark:text-gray-300">👤 Информация о пользователе</h3>
                  <button onClick={() => setViewingUser(null)} className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 text-xl">&times;</button>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">ID</span>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{viewingUser.id}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">Имя пользователя</span>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{viewingUser.username}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">Email</span>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{viewingUser.email}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">ФИО</span>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{viewingUser.full_name || '—'}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">Телефон</span>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{viewingUser.phone || '—'}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">Роль</span>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{viewingUser.role === 'admin' ? 'Администратор' : viewingUser.role === 'responsible' ? 'Ответственный' : 'Пользователь'}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">Статус</span>
                    <p className="text-sm font-medium">
                      <span className={`px-2 py-0.5 text-xs rounded-full ${viewingUser.is_active ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'}`}>
                        {viewingUser.is_active ? 'Активен' : 'Неактивен'}
                      </span>
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">Дата регистрации</span>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{viewingUser.created_at ? new Date(viewingUser.created_at).toLocaleDateString('ru-RU') : '—'}</p>
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
                  <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Подразделения и размещения</h2>
                  <button
                    onClick={() => { setShowDeptForm(true); setEditingDept(null); setDeptFormData({ name: '', code: '', head: '', phone: '', email: '', location: '' }); }}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition text-sm"
                  >
                    ➕ Добавить подразделение
                  </button>
                </div>

                {showDeptForm && (
                  <div className="bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4 mb-4">
                    <h3 className="font-medium text-gray-700 dark:text-gray-300 mb-3">{editingDept ? 'Редактировать подразделение' : 'Новое подразделение'}</h3>
                    <div className="grid grid-cols-2 gap-3">
                      <input type="text" placeholder="Название *" value={deptFormData.name} onChange={(e) => setDeptFormData({...deptFormData, name: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
                      <input type="text" placeholder="Код *" value={deptFormData.code} onChange={(e) => setDeptFormData({...deptFormData, code: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
                      <input type="text" placeholder="Руководитель" value={deptFormData.head} onChange={(e) => setDeptFormData({...deptFormData, head: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
                      <input type="text" placeholder="Телефон" value={deptFormData.phone} onChange={(e) => setDeptFormData({...deptFormData, phone: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
                      <input type="email" placeholder="Email" value={deptFormData.email} onChange={(e) => setDeptFormData({...deptFormData, email: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
                      <input type="text" placeholder="Местоположение" value={deptFormData.location} onChange={(e) => setDeptFormData({...deptFormData, location: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
                    </div>
                    <div className="flex gap-2 mt-3">
                      <button onClick={editingDept ? handleUpdateDepartment : handleCreateDepartment} className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 transition">{editingDept ? 'Сохранить' : 'Создать'}</button>
                      <button onClick={() => { setShowDeptForm(false); setEditingDept(null); }} className="bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-200 px-4 py-1.5 rounded text-sm hover:bg-gray-400 dark:hover:bg-gray-500 transition">Отмена</button>
                    </div>
                  </div>
                )}

                <div className="mb-4">
                  <input
                    type="text"
                    placeholder="Поиск подразделений..."
                    value={deptSearch}
                    onChange={(e) => { setDeptSearch(e.target.value); }}
                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg w-full text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                  />
                </div>

                {deptLoading ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">Загрузка...</div>
                ) : deptTree.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">Нет подразделений</div>
                ) : (
                  <div className="space-y-2">
                    {deptTree.filter(d => 
                      !deptSearch || 
                      d.name.toLowerCase().includes(deptSearch.toLowerCase()) ||
                      d.code.toLowerCase().includes(deptSearch.toLowerCase()) ||
                      (d.head || '').toLowerCase().includes(deptSearch.toLowerCase()) ||
                      (d.location || '').toLowerCase().includes(deptSearch.toLowerCase())
                    ).map((dept) => {
                      const isExpanded = expandedDepts.has(dept.id);
                      const sortedRooms = [...(dept.rooms || [])].sort((a, b) => (a.name || '').localeCompare(b.name || ''));
                      return (
                        <div key={dept.id} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                          <div className="flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-750 hover:bg-gray-100 dark:hover:bg-gray-700 transition cursor-pointer" onClick={() => toggleDeptRooms(dept.id)}>
                            <div className="flex items-center gap-4 flex-1 min-w-0">
                              <span className="text-purple-600 dark:text-purple-400 text-sm flex-shrink-0">{isExpanded ? '▼' : '▶'}</span>
                              <span className="font-mono text-sm font-medium text-gray-900 dark:text-gray-100 flex-shrink-0 bg-purple-50 dark:bg-purple-900/30 px-2 py-0.5 rounded">{dept.code}</span>
                              <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{dept.name}</span>
                              <span className="text-sm text-gray-600 dark:text-gray-400 truncate hidden sm:inline">{dept.head || '—'}</span>
                              <span className="text-sm text-gray-500 dark:text-gray-400 truncate hidden md:inline">{dept.location || '—'}</span>
                              <span className="text-xs text-gray-400 dark:text-gray-500 flex-shrink-0 ml-auto hidden sm:inline">{sortedRooms.length} комн.</span>
                            </div>
                            <div className="flex items-center gap-1 flex-shrink-0 ml-4">
                              <button
                                onClick={(e) => { e.stopPropagation(); setEditingDept(dept); setDeptFormData({ name: dept.name, code: dept.code, head: dept.head || '', phone: dept.phone || '', email: dept.email || '', location: dept.location || '' }); setShowDeptForm(true); }}
                                className="p-1.5 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded transition"
                                title="Редактировать подразделение"
                              >
                                ✏️
                              </button>
                              <button
                                onClick={(e) => { e.stopPropagation(); handleDeleteDepartment(dept.id); }}
                                className="p-1.5 text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition"
                                title="Удалить подразделение"
                              >
                                🗑️
                              </button>
                            </div>
                          </div>
                          {isExpanded && (
                            <div className="px-4 py-3 bg-white border-t border-gray-100">
                              <div className="flex justify-between items-center mb-3">
                                <span className="text-xs font-semibold text-purple-700 uppercase tracking-wide">Кабинеты подразделения {dept.name}</span>
                                <button
                                  onClick={() => { setEditingRoom(null); setRoomFormData({ name: '', floor: '', building: '' }); setRoomDeptId(dept.id); setShowRoomForm(true); }}
                                  className="bg-purple-600 text-white px-3 py-1.5 rounded text-xs font-medium hover:bg-purple-700 transition"
                                >
                                  ➕ Добавить кабинет
                                </button>
                              </div>

                              {showRoomForm && roomDeptId === dept.id && !editingRoom && (
                                <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 mb-3">
                                  <div className="text-xs font-semibold text-purple-800 mb-2">Новый кабинет</div>
                                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-2">
                                    <input type="text" placeholder="Название *" value={roomFormData.name} onChange={(e) => setRoomFormData({...roomFormData, name: e.target.value})} className="px-3 py-1.5 border border-purple-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-purple-400" />
                                    <div className="flex flex-col gap-1">
                                      <label className="text-xs text-purple-700 font-medium">Этаж</label>
                                      <input type="text" placeholder="напр. 2" value={roomFormData.floor} onChange={(e) => setRoomFormData({...roomFormData, floor: e.target.value})} className="px-3 py-1.5 border border-purple-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-purple-400" />
                                    </div>
                                    <div className="flex flex-col gap-1">
                                      <label className="text-xs text-purple-700 font-medium">Корпус / Здание</label>
                                      <input type="text" placeholder="напр. Корп. А" value={roomFormData.building} onChange={(e) => setRoomFormData({...roomFormData, building: e.target.value})} className="px-3 py-1.5 border border-purple-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-purple-400" />
                                    </div>
                                  </div>
                                  <div className="flex gap-2">
                                    <button onClick={handleCreateRoom} className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 transition">Добавить</button>
                                    <button onClick={() => { setShowRoomForm(false); setEditingRoom(null); setRoomDeptId(null); setRoomFormData({ name: '', floor: '', building: '' }); }} className="bg-gray-300 text-gray-700 px-4 py-1.5 rounded text-sm hover:bg-gray-400 transition">Отмена</button>
                                  </div>
                                </div>
                              )}

                              {editingRoom && roomDeptId === dept.id && (
                                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-3">
                                  <div className="text-xs font-semibold text-yellow-800 mb-2">Редактирование: {editingRoom.name}</div>
                                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-2">
                                    <input type="text" placeholder="Название *" value={roomFormData.name} onChange={(e) => setRoomFormData({...roomFormData, name: e.target.value})} className="px-3 py-1.5 border border-yellow-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-yellow-400" />
                                    <div className="flex flex-col gap-1">
                                      <label className="text-xs text-yellow-700 font-medium">Этаж</label>
                                      <input type="text" placeholder="напр. 2" value={roomFormData.floor} onChange={(e) => setRoomFormData({...roomFormData, floor: e.target.value})} className="px-3 py-1.5 border border-yellow-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-yellow-400" />
                                    </div>
                                    <div className="flex flex-col gap-1">
                                      <label className="text-xs text-yellow-700 font-medium">Корпус / Здание</label>
                                      <input type="text" placeholder="напр. Корп. А" value={roomFormData.building} onChange={(e) => setRoomFormData({...roomFormData, building: e.target.value})} className="px-3 py-1.5 border border-yellow-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-yellow-400" />
                                    </div>
                                  </div>
                                  <div className="flex gap-2">
                                    <button onClick={handleUpdateRoom} className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 transition">Сохранить</button>
                                    <button onClick={() => { setShowRoomForm(false); setEditingRoom(null); setRoomDeptId(null); setRoomFormData({ name: '', floor: '', building: '' }); }} className="bg-gray-300 text-gray-700 px-4 py-1.5 rounded text-sm hover:bg-gray-400 transition">Отмена</button>
                                  </div>
                                </div>
                              )}

                              {sortedRooms.length === 0 ? (
                                <div className="text-center py-4 text-gray-400 text-sm">Нет кабинетов</div>
                              ) : (
                                <div className="flex flex-wrap gap-2">
                                  {sortedRooms.map((room) => (
                                    <div key={room.id} className="inline-flex items-center gap-1.5 bg-purple-50 border border-purple-200 rounded-full pl-3 pr-1 py-1">
                                      <div className="flex items-center gap-1.5">
                                        <span className="text-sm font-medium text-gray-900">{room.name}</span>
                                        {room.floor && <span className="text-xs text-purple-600 bg-purple-100 px-1.5 py-0.5 rounded-full">Эт. {room.floor}</span>}
                                        {room.building && <span className="text-xs text-purple-600 bg-purple-100 px-1.5 py-0.5 rounded-full">Корп. {room.building}</span>}
                                      </div>
                                      <button
                                        onClick={() => handleEditRoom(dept, room)}
                                        className="p-1 text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded-full transition flex-shrink-0"
                                        title="Редактировать"
                                      >
                                        ✏️
                                      </button>
                                      <button
                                        onClick={() => handleDeleteRoom(room.id)}
                                        className="p-1 text-red-600 hover:text-red-900 hover:bg-red-100 rounded-full transition flex-shrink-0"
                                        title="Удалить"
                                      >
                                        🗑️
                                      </button>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}

                <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <h3 className="text-sm font-medium text-blue-900 dark:text-blue-300 mb-2">📋 Управление размещениями</h3>
                  <p className="text-xs text-blue-700 dark:text-blue-400 mb-2">На странице активов используйте фильтры по подразделению и сотруднику для поиска. Для назначения актива используйте редактирование актива.</p>
                  <p className="text-xs text-blue-700 dark:text-blue-400">Сотрудники, связанные с подразделением, автоматически отображаются при выборе этого подразделения.</p>
                </div>
              </>
            )}

            {activeTab === 'employees' && (
              <>
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Сотрудники</h2>
                  <button
                    onClick={() => { setShowEmpForm(true); setEditingEmp(null); setEmpFormData({ first_name: '', last_name: '', middle_name: '', department_id: 0, position: '', phone: '', email: '', employee_number: '' }); }}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition text-sm"
                  >
                    ➕ Добавить сотрудника
                  </button>
                </div>

                {showEmpForm && (
                  <div className="bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4 mb-4">
                    <h3 className="font-medium text-gray-700 dark:text-gray-300 mb-3">{editingEmp ? 'Редактировать сотрудника' : 'Новый сотрудник'}</h3>
                    <div className="grid grid-cols-2 gap-3">
                      <input type="text" placeholder="Фамилия *" value={empFormData.last_name} onChange={(e) => setEmpFormData({...empFormData, last_name: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
                      <input type="text" placeholder="Имя *" value={empFormData.first_name} onChange={(e) => setEmpFormData({...empFormData, first_name: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
                      <input type="text" placeholder="Отчество" value={empFormData.middle_name} onChange={(e) => setEmpFormData({...empFormData, middle_name: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
                      <select value={empFormData.department_id} onChange={(e) => setEmpFormData({...empFormData, department_id: Number(e.target.value)})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                        <option value={0}>Выберите подразделение</option>
                        {deptTree.map(d => <option key={d.id} value={d.id}>{d.name} ({d.code})</option>)}
                      </select>
                      <input type="text" placeholder="Должность" value={empFormData.position} onChange={(e) => setEmpFormData({...empFormData, position: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
                      <input type="text" placeholder="Телефон" value={empFormData.phone} onChange={(e) => setEmpFormData({...empFormData, phone: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
                      <input type="email" placeholder="Email" value={empFormData.email} onChange={(e) => setEmpFormData({...empFormData, email: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
                      <input type="text" placeholder="Табельный номер" value={empFormData.employee_number} onChange={(e) => setEmpFormData({...empFormData, employee_number: e.target.value})} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
                    </div>
                    <div className="flex gap-2 mt-3">
                      <button onClick={editingEmp ? handleUpdateEmployee : handleCreateEmployee} className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 transition">{editingEmp ? 'Сохранить' : 'Создать'}</button>
                      <button onClick={() => { setShowEmpForm(false); setEditingEmp(null); }} className="bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-200 px-4 py-1.5 rounded text-sm hover:bg-gray-400 dark:hover:bg-gray-500 transition">Отмена</button>
                    </div>
                  </div>
                )}

                <div className="flex gap-3 mb-4">
                  <input
                    type="text"
                    placeholder="Поиск сотрудников..."
                    value={empSearch}
                    onChange={(e) => setEmpSearch(e.target.value)}
                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg flex-1 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                  />
                  <select
                    value={empDeptFilter}
                    onChange={(e) => setEmpDeptFilter(e.target.value)}
                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                  >
                    <option value="">Все подразделения</option>
                    {deptTree.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </select>
                </div>

                {empLoading ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">Загрузка...</div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                      <thead className="bg-gray-50 dark:bg-gray-700">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">ФИО</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Должность</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Подразделение</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Телефон</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Email</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Действия</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                        {employees.length === 0 ? (
                          <tr><td colSpan={6} className="px-4 py-4 text-center text-gray-500 dark:text-gray-400 text-sm">Нет сотрудников</td></tr>
                        ) : (
                          employees.map((emp) => (
                            <tr key={emp.id} className="hover:bg-gray-50 dark:hover:bg-gray-750 transition">
                              <td className="px-4 py-2 text-sm text-gray-900 dark:text-gray-100">{emp.first_name} {emp.last_name}{emp.middle_name ? ` ${emp.middle_name}` : ''}</td>
                              <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">{emp.position || '—'}</td>
                              <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">{emp.department_name || emp.department_code || '—'}</td>
                              <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">{emp.phone || '—'}</td>
                              <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">{emp.email || '—'}</td>
                              <td className="px-4 py-2 text-right text-sm">
                                <button onClick={() => { setEditingEmp(emp); setEmpFormData({ first_name: emp.first_name, last_name: emp.last_name, middle_name: emp.middle_name || '', department_id: emp.department_id || 0, position: emp.position || '', phone: emp.phone || '', email: emp.email || '', employee_number: emp.employee_number || '' }); setShowEmpForm(true); }} className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 mr-3">✏️</button>
                                <button onClick={() => handleDeleteEmployee(emp.id)} className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300">🗑️</button>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                )}

                <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-lg">
                  <h3 className="text-sm font-medium text-green-900 dark:text-green-300 mb-2">👤 Сотрудники и активы</h3>
                  <p className="text-xs text-green-700 dark:text-green-400">Сотрудники могут быть назначены ответственными за активы. При назначении актива сотруднику его ФИО автоматически подтягивается из списка сотрудников подразделения.</p>
                </div>
              </>
            )}

            {activeTab === 'password-requests' && (
              <>
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">🔑 Заявки на сброс пароля</h2>
                  <button
                    onClick={fetchPasswordRequests}
                    disabled={requestsLoading}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm disabled:opacity-50"
                  >
                    {requestsLoading ? 'Загрузка...' : '🔄 Обновить'}
                  </button>
                </div>

                {/* Filter buttons */}
                <div className="flex gap-2 mb-4">
                  {(['all', 'pending', 'approved', 'rejected'] as const).map((filter) => {
                    const labels = { all: 'Все', pending: 'Ожидают', approved: 'Одобреные', rejected: 'Отклонённые' };
                    const counts = {
                      all: passwordRequests.length,
                      pending: passwordRequests.filter(r => r.status === 'pending').length,
                      approved: passwordRequests.filter(r => r.status === 'approved').length,
                      rejected: passwordRequests.filter(r => r.status === 'rejected').length,
                    };
                    return (
                      <button
                        key={filter}
                        onClick={() => setRequestsFilter(filter)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                          requestsFilter === filter
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                        }`}
                      >
                        {labels[filter]} ({counts[filter]})
                      </button>
                    );
                  })}
                </div>

                {requestsLoading ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">Загрузка заявок...</div>
                ) : passwordRequests.filter(r => requestsFilter === 'all' || r.status === requestsFilter).length === 0 ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    {requestsFilter === 'all' ? 'Заявок пока нет' : 'Нет заявок с таким статусом'}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {passwordRequests
                      .filter(r => requestsFilter === 'all' || r.status === requestsFilter)
                      .sort((a, b) => {
                        const order = { pending: 0, approved: 1, rejected: 2 };
                        return order[a.status] - order[b.status];
                      })
                      .map((req) => {
                        const statusMap = {
                          pending: { text: 'Ожидает', class: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300' },
                          approved: { text: 'Одобрен', class: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' },
                          rejected: { text: 'Отклонён', class: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300' },
                        };
                        const status = statusMap[req.status];
                        return (
                          <div key={req.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition">
                            <div className="flex justify-between items-start mb-2">
                              <div>
                                <h3 className="font-medium text-gray-900 dark:text-gray-100">{req.username}</h3>
                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                  {req.full_name && <span>{req.full_name} | </span>}
                                  {req.email && <span>{req.email} | </span>}
                                  {new Date(req.created_at).toLocaleString('ru-RU')}
                                </p>
                              </div>
                              <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${status.class}`}>
                                {status.text}
                              </span>
                            </div>
                            <div className="bg-gray-50 dark:bg-gray-700 rounded p-2 mb-3">
                              <p className="text-sm text-gray-700 dark:text-gray-300">{req.reason}</p>
                            </div>
                            {req.status === 'pending' && (
                              <div className="flex gap-2">
                                <button
                                  onClick={() => handlePasswordRequestAction(req.id, 'approve')}
                                  className="bg-green-600 text-white px-3 py-1.5 rounded text-xs font-medium hover:bg-green-700 transition"
                                >
                                  ✅ Одобрить
                                </button>
                                <button
                                  onClick={() => handlePasswordRequestAction(req.id, 'reject')}
                                  className="bg-red-600 text-white px-3 py-1.5 rounded text-xs font-medium hover:bg-red-700 transition"
                                >
                                  ❌ Отклонить
                                </button>
                              </div>
                            )}
                            {req.admin_comment && (
                              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                                💬 {req.admin_comment}
                              </p>
                            )}
                          </div>
                        );
                      })}
                  </div>
                )}
              </>
            )}

            <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <h3 className="text-lg font-medium text-blue-900 dark:text-blue-300 mb-2">ℹ️ Информация</h3>
              <ul className="list-disc list-inside text-sm text-blue-700 dark:text-blue-400 space-y-1">
                <li>Здесь вы можете управлять пользователями, подразделениями и сотрудниками</li>
                <li>Подразделения используются для размещения активов</li>
                <li>Сотрудники могут быть назначены ответственными за активы</li>
                <li>Начальный администратор: <strong className="text-blue-900 dark:text-blue-200">admin</strong> (пароль: <strong className="text-blue-900 dark:text-blue-200">admin123</strong>)</li>
              </ul>
            </div>
            </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default AdminPanel;
