// frontend/src/pages/RoomInventoryPrint.tsx
import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { FileText, Printer, CheckCircle2, Archive, Send, History } from 'lucide-react';
import toast from 'react-hot-toast';
import { TransferActsTab } from '../components/placements/TransferActsTab';
import { TransferHistoryTab } from '../components/placements/TransferHistoryTab';

interface Room {
  id: number;
  name: string;
  floor: string;
  building: string;
  asset_count: number;
}

interface Department {
  id: number;
  name: string;
  code: string;
}

interface Employee {
  id: number;
  full_name: string;
  position: string;
  department_name: string;
  department_code: string;
}

interface RoomInventoryPrint {
  id: number;
  room_id: number;
  room_name: string;
  department_name: string | null;
  employee_id: number | null;
  employee_name: string | null;
  employee_position: string | null;
  asset_count: number;
  file_path: string | null;
  signed: boolean;
  signed_at: string | null;
  signed_by: string | null;
  created_by: string | null;
  created_at: string;
  is_archived?: boolean;
  archived_at?: string | null;
}

type TabType = 'print' | 'list' | 'transfer' | 'history';

const RoomInventoryPrint: React.FC = () => {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>('print');
  const [departments, setDepartments] = useState<Department[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [selectedDept, setSelectedDept] = useState<number | null>(null);
  const [selectedRoom, setSelectedRoom] = useState<number | null>(null);
  const [selectedEmployee, setSelectedEmployee] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [prints, setPrints] = useState<RoomInventoryPrint[]>([]);
  const [loadingPrints, setLoadingPrints] = useState(false);

  const loadPrints = async () => {
    if (!token) return;
    setLoadingPrints(true);
    try {
      const res = await fetch('/api/admin/placements/inventory-prints', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setPrints(data);
      }
    } catch (e) {
      console.error('Error loading prints:', e);
    } finally {
      setLoadingPrints(false);
    }
  };

  useEffect(() => {
    if (!token) return;
    fetch('/api/admin/placements/options', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .catch(() => [] as Department[])
      .then((data) => setDepartments(data));
  }, [token]);

  useEffect(() => {
    if (!token) return;
    fetch('/api/admin/employees/options', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .catch(() => [] as Employee[])
      .then((data) => setEmployees(data));
  }, [token]);

  useEffect(() => {
    if (!selectedDept || !token) {
      setRooms([]);
      setSelectedRoom(null);
      return;
    }
    setLoading(true);
    setError(null);
    fetch(`/api/admin/placements/${selectedDept}/rooms-with-assets`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => {
        if (!r.ok) throw new Error('Ошибка загрузки кабинетов');
        return r.json();
      })
      .then((data) => setRooms(data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [selectedDept, token]);

  useEffect(() => {
    loadPrints();
  }, []);

  const handlePrint = async () => {
    if (!selectedRoom || !token) return;
    setGenerating(true);
    setError(null);
    setSuccess(false);

    try {
      const response = await fetch(`/api/admin/placements/${selectedRoom}/print/inventory`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ employee_id: selectedEmployee || null }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Ошибка генерации описи');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const filename = response.headers.get('Content-Disposition')
        ?.match(/filename="?(.+)"?/)?.[1]
        || 'опись.xlsx';
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      setTimeout(() => {
        setSuccess(true);
        loadPrints();
      }, 500);
    } catch (e: any) {
      setError(e.message || 'Не удалось сгенерировать опись');
    } finally {
      setGenerating(false);
    }
  };

  const handleConfirm = async (printId: number) => {
    if (!token) return;
    if (!window.confirm('Подтвердить подписание? Активам в кабинете будет присвоен сотрудник-подписант.')) return;

    try {
      const res = await fetch(`/api/admin/placements/inventory-prints/${printId}/confirm`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        toast.success('Опись подтверждена');
        loadPrints();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Ошибка подтверждения');
      }
    } catch (e: any) {
      toast.error(e.message || 'Ошибка соединения');
    }
  };

  const handleArchive = async (printId: number) => {
    if (!token) return;
    if (!window.confirm('Архивировать опись? Активам ничего не присвоится.')) return;

    try {
      const res = await fetch(`/api/admin/placements/inventory-prints/${printId}/archive`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        toast.success('Опись архивирована');
        // Мгновенно убираем опись из списка, затем синхронизируем с сервером
        setPrints((prev) => prev.filter((p) => p.id !== printId));
        loadPrints();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Ошибка архивирования');
      }
    } catch (e: any) {
      toast.error(e.message || 'Ошибка соединения');
    }
  };

  const selectedEmployeeData = employees.find((e) => e.id === selectedEmployee);
  const employeeDisplay = selectedEmployeeData
    ? `${selectedEmployeeData.full_name} — ${selectedEmployeeData.position || '—'}`
    : '—';

  const tabs = [
    { id: 'print' as TabType, label: 'Распечатать опись', icon: <Printer className="w-4 h-4" /> },
    { id: 'list' as TabType, label: `Список описей (${prints.length})`, icon: <FileText className="w-4 h-4" /> },
    { id: 'transfer' as TabType, label: 'Акты передачи', icon: <Send className="w-4 h-4" /> },
    { id: 'history' as TabType, label: 'История передач', icon: <History className="w-4 h-4" /> },
  ];

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">📋 Описи помещений</h1>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-200 dark:border-gray-700">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition ${
              activeTab === tab.id
                ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB: PRINT */}
      {activeTab === 'print' && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
            <Printer className="w-5 h-5" />
            Распечатка описи помещения
          </h2>

          {error && (
            <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg mb-4">
              {error}
            </div>
          )}

          {success && (
            <div className="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-700 text-green-700 dark:text-green-300 px-4 py-3 rounded-lg mb-4">
              ✅ Файл описи успешно скачан.
            </div>
          )}

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Подразделение
            </label>
            <select
              value={selectedDept ?? ''}
              onChange={(e) => setSelectedDept(e.target.value ? Number(e.target.value) : null)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
              disabled={generating}
            >
              <option value="">— Выберите подразделение —</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.code})
                </option>
              ))}
            </select>
          </div>

          {rooms.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Кабинет
              </label>

              {loading ? (
                <div className="flex justify-center py-4">
                  <div className="text-gray-500">⏳ Загрузка...</div>
                </div>
              ) : (
                <>
                  <select
                    value={selectedRoom ?? ''}
                    onChange={(e) => setSelectedRoom(e.target.value ? Number(e.target.value) : null)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 mb-4"
                    disabled={generating}
                  >
                    <option value="">— Выберите кабинет —</option>
                    {rooms.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.name}
                        {r.floor ? ` (эт. ${r.floor})` : ''}
                        — {r.asset_count} {r.asset_count === 1 ? 'актив' : r.asset_count < 5 ? 'актива' : 'активов'}
                      </option>
                    ))}
                  </select>

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Подписант (должность, ФИО)
                    </label>
                    <select
                      value={selectedEmployee ?? ''}
                      onChange={(e) => setSelectedEmployee(e.target.value ? Number(e.target.value) : null)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
                      disabled={generating}
                    >
                      <option value="">— Не выбран —</option>
                      {employees.map((e) => (
                        <option key={e.id} value={e.id}>
                          {e.full_name} — {e.position || '—'} ({e.department_name || '—'})
                        </option>
                      ))}
                    </select>
                    {selectedEmployeeData && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        Будет подписант: <span className="font-medium">{employeeDisplay}</span>
                      </p>
                    )}
                  </div>

                  <button
                    onClick={handlePrint}
                    disabled={!selectedRoom || generating}
                    className={`w-full py-3 px-4 rounded-lg text-white font-medium transition ${
                      !selectedRoom || generating
                        ? 'bg-gray-400 cursor-not-allowed'
                        : 'bg-blue-600 hover:bg-blue-700'
                    }`}
                  >
                    {generating ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Генерация...
                      </span>
                    ) : (
                      '📥 Скачать опись'
                    )}
                  </button>
                </>
              )}
            </div>
          )}

          {!loading && rooms.length === 0 && selectedDept !== null && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
              <p className="text-gray-500 dark:text-gray-400">
                В этом подразделении нет активных кабинетов.
              </p>
            </div>
          )}
        </div>
      )}

      {/* TAB: LIST */}
      {activeTab === 'list' && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Сформированные описи
          </h2>

          {loadingPrints ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
            </div>
          ) : prints.length === 0 ? (
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">
              Описей пока нет
            </p>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">№</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Кабинет</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Дата и время</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Подписант</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Активов</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Статус</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {prints.map((print, idx) => (
                    <tr key={print.id} className={`border-b border-gray-100 dark:border-gray-700 ${print.signed ? 'bg-green-50 dark:bg-green-900/10' : ''}`}>
                      <td className="px-4 py-3 text-gray-500">{idx + 1}</td>
                      <td className="px-4 py-3 text-gray-900 dark:text-gray-100">
                        {new Date(print.created_at).toLocaleDateString('ru-RU')}
                        <br />
                        <span className="text-xs text-gray-500">{new Date(print.created_at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}</span>
                      </td>
                      <td className="px-4 py-3 text-gray-900 dark:text-gray-100 font-medium">
                        {print.room_name}
                        {print.department_name && (
                          <span className="block text-xs text-gray-500">{print.department_name}</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                        {print.employee_name || '—'}
                      </td>
                      <td className="px-4 py-3 text-gray-700 dark:text-gray-300">{print.asset_count}</td>
                      <td className="px-4 py-3">
                        {print.signed ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">
                            <CheckCircle2 className="w-3 h-3" /> Подписана
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300">
                            <Archive className="w-3 h-3" /> Не подписана
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {!print.signed ? (
                          <div className="flex gap-1">
                            <button
                              onClick={() => handleConfirm(print.id)}
                              className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition"
                            >
                              Подписать
                            </button>
                            <button
                              onClick={() => handleArchive(print.id)}
                              className="px-2 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600 transition"
                            >
                              Архив
                            </button>
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400">Подписана</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB: TRANSFER ACTS */}
      {activeTab === 'transfer' && (
        <TransferActsTab
          departments={departments}
          rooms={rooms}
          employees={employees}
          token={token}
          selectedDept={selectedDept}
          setSelectedDept={setSelectedDept}
          selectedRoom={selectedRoom}
          setSelectedRoom={setSelectedRoom}
        />
      )}

      {/* TAB: TRANSFER HISTORY */}
      {activeTab === 'history' && <TransferHistoryTab token={token} />}
    </div>
  );
};

export default RoomInventoryPrint;