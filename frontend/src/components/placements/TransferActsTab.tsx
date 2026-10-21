// frontend/src/components/placements/TransferActsTab.tsx
import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import { useAuth } from '../../hooks/useAuth';
import { FileText, CheckCircle2, Archive, Download, Upload, Search, Send } from 'lucide-react';

interface Employee {
  id: number;
  full_name: string;
  position: string;
  department_name: string;
}

interface Department {
  id: number;
  name: string;
  code: string;
}

interface Room {
  id: number;
  name: string;
  floor?: string;
  building?: string;
  asset_count: number;
}

interface RoomAsset {
  id: number;
  name: string;
  inventory_number: string;
  quantity: number;
  model: string;
  serial_number: string;
  asset_type: string;
  employee_name?: string | null;
  responsible_person?: string;
}

interface TransferActItem {
  id: number;
  name: string;
  inventory_number: string;
  quantity: number;
  model: string;
  serial_number: string;
}

interface TransferActAttachment {
  id: string;
  filename: string;
  uploaded_at: string;
}

interface TransferAct {
  id: number;
  act_number: string;
  act_date: string | null;
  employee_id: number | null;
  employee_name: string | null;
  employee_position: string | null;
  department_name: string | null;
  room_name: string | null;
  asset_count: number;
  assets: TransferActItem[];
  attachments: TransferActAttachment[];
  signed: boolean;
  signed_at: string | null;
  is_archived: boolean;
  created_at: string | null;
}

interface Props {
  departments: Department[];
  rooms: Room[];
  employees: Employee[];
  token: string | null;
  selectedDept: number | null;
  setSelectedDept: (v: number | null) => void;
  selectedRoom: number | null;
  setSelectedRoom: (v: number | null) => void;
  loadRooms?: () => void;
}

const api = (path: string, init?: RequestInit, token?: string | null) =>
  fetch(path, {
    ...init,
    headers: {
      ...(init?.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

export const TransferActsTab: React.FC<Props> = ({
  departments,
  rooms,
  employees,
  token,
  selectedDept,
  setSelectedDept,
  selectedRoom,
  setSelectedRoom,
}) => {
  const { token: authToken } = useAuth();
  const effectiveToken = token ?? authToken;

  const [acts, setActs] = useState<TransferAct[]>([]);
  const [loadingActs, setLoadingActs] = useState(false);

  // Форма
  const [search, setSearch] = useState('');
  const [foundAssets, setFoundAssets] = useState<RoomAsset[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [selectedEmployee, setSelectedEmployee] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);

  const [uploadingActId, setUploadingActId] = useState<number | null>(null);

  const loadActs = useCallback(async () => {
    if (!effectiveToken) return;
    setLoadingActs(true);
    try {
      const res = await api('/api/admin/transfer-acts', {}, effectiveToken);
      if (res.ok) {
        const data = await res.json();
        setActs(data);
      } else {
        toast.error('Ошибка загрузки актов');
      }
    } catch (e: any) {
      toast.error(e.message || 'Ошибка соединения');
    } finally {
      setLoadingActs(false);
    }
  }, [effectiveToken]);

  useEffect(() => {
    loadActs();
  }, [loadActs]);

  // Поиск активов (по всем активам)
  const handleSearch = async () => {
    if (!effectiveToken) return;
    setSearching(true);
    try {
      let query = '';
      if (search.trim()) {
        query = `&search=${encodeURIComponent(search.trim())}`;
      } else if (selectedRoom) {
        // Ищем активы кабинета через placements endpoint
        const res = await api(`/api/admin/placements/${selectedRoom}/assets`, {}, effectiveToken);
        if (res.ok) {
          setFoundAssets(await res.json());
          return;
        }
      }
      const res = await api(`/api/admin/assets?limit=200&include_hidden=false${query}`, {}, effectiveToken);
      if (!res.ok) throw new Error('Ошибка поиска активов');
      const data = await res.json();
      const items = Array.isArray(data) ? data : data.items || [];
      setFoundAssets(items);
    } catch (e: any) {
      toast.error(e.message || 'Ошибка поиска активов');
    } finally {
      setSearching(false);
    }
  };

  useEffect(() => {
    if (selectedRoom) handleSearch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedRoom]);

  const toggleAsset = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectVisible = () => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      foundAssets.forEach((a) => next.add(a.id));
      return next;
    });
  };

  const clearSelection = () => setSelectedIds(new Set());

  const createAct = async () => {
    if (!effectiveToken) return;
    if (selectedIds.size === 0) {
      toast.error('Выберите хотя бы один актив');
      return;
    }
    if (!selectedEmployee) {
      toast.error('Выберите сотрудника-получателя');
      return;
    }
    setCreating(true);
    try {
      const res = await api(
        '/api/admin/transfer-acts',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            asset_ids: Array.from(selectedIds),
            employee_id: selectedEmployee,
            room_id: selectedRoom || null,
          }),
        },
        effectiveToken,
      );
      if (res.ok) {
        const data = await res.json();
        toast.success(`Акт ${data.act?.act_number || ''} сформирован`);
        setSelectedIds(new Set());
        setSearch('');
        setFoundAssets([]);
        await loadActs();
        // Скачиваем файл акта сразу
        if (data.act?.id) {
          window.open(`/api/admin/transfer-acts/${data.act.id}/download`, '_blank');
        }
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Ошибка формирования акта');
      }
    } catch (e: any) {
      toast.error(e.message || 'Ошибка соединения');
    } finally {
      setCreating(false);
    }
  };

  const confirmAct = async (act: TransferAct) => {
    if (!effectiveToken) return;
    if (!window.confirm(`Подписать акт ${act.act_number}? Сотрудник будет проставлен в данных активов.`)) return;
    try {
      const res = await api(`/api/admin/transfer-acts/${act.id}/confirm`, { method: 'POST' }, effectiveToken);
      if (res.ok) {
        const data = await res.json();
        toast.success(`Акт подписан (активов обновлено: ${data.assets_updated})`);
        loadActs();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Ошибка подписания');
      }
    } catch (e: any) {
      toast.error(e.message || 'Ошибка соединения');
    }
  };

  const archiveAct = async (act: TransferAct) => {
    if (!effectiveToken) return;
    if (!window.confirm(`Архивировать акт ${act.act_number}?`)) return;
    try {
      const res = await api(`/api/admin/transfer-acts/${act.id}/archive`, { method: 'POST' }, effectiveToken);
      if (res.ok) {
        toast.success('Акт архивирован');
        loadActs();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Ошибка архивирования');
      }
    } catch (e: any) {
      toast.error(e.message || 'Ошибка соединения');
    }
  };

  const uploadScan = async (act: TransferAct, files: FileList | null) => {
    if (!effectiveToken || !files || files.length === 0) return;
    for (const file of Array.from(files)) {
      setUploadingActId(act.id);
      const formData = new FormData();
      formData.append('file', file);
      try {
        const res = await api(
          `/api/admin/transfer-acts/${act.id}/attachments`,
          { method: 'POST', body: formData },
          effectiveToken,
        );
        if (res.ok) {
          toast.success(`Скан ${file.name} прикреплён`);
        } else {
          const err = await res.json().catch(() => ({}));
          toast.error(err.detail || `Ошибка загрузки ${file.name}`);
        }
      } catch (e: any) {
        toast.error(e.message || 'Ошибка соединения');
      }
    }
    setUploadingActId(null);
    loadActs();
  };

  const attachmentUrl = (act: TransferAct, attId: string) =>
    `/api/admin/transfer-acts/${act.id}/attachments/${attId}`;

  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
        <Send className="w-5 h-5" />
        Акты передачи имущества в пользование
      </h2>

      {/* Форма формирования акта */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Подразделение (опционально)
            </label>
            <select
              value={selectedDept ?? ''}
              onChange={(e) => {
                setSelectedDept(e.target.value ? Number(e.target.value) : null);
                setSelectedRoom(null);
              }}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">— Не выбрано —</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.code})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Кабинет (опционально)
            </label>
            <select
              value={selectedRoom ?? ''}
              onChange={(e) => setSelectedRoom(e.target.value ? Number(e.target.value) : null)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">— Все активы (поиск ниже) —</option>
              {rooms.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name} ({r.asset_count})
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Поиск активов (флешки, токены, инструмент, сумки, расходники и т.д.)
          </label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Например: флешка, токен, инструмент..."
                className="w-full pl-9 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={searching}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
            >
              {searching ? 'Поиск...' : 'Найти'}
            </button>
          </div>
        </div>

        {foundAssets.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Найдено: {foundAssets.length} · выбрано: {selectedIds.size}
              </span>
              <div className="flex gap-2">
                <button onClick={selectVisible} className="text-xs text-blue-600 hover:underline">
                  Выбрать все
                </button>
                <button onClick={clearSelection} className="text-xs text-gray-500 hover:underline">
                  Сбросить
                </button>
              </div>
            </div>
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg max-h-64 overflow-y-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-900">
                    <th className="w-10 px-2 py-2" />
                    <th className="text-left px-2 py-2 font-medium text-gray-600 dark:text-gray-300">Наименование</th>
                    <th className="text-left px-2 py-2 font-medium text-gray-600 dark:text-gray-300">Инв. №</th>
                    <th className="text-left px-2 py-2 font-medium text-gray-600 dark:text-gray-300">Модель</th>
                    <th className="text-left px-2 py-2 font-medium text-gray-600 dark:text-gray-300">Серийный №</th>
                    <th className="text-left px-2 py-2 font-medium text-gray-600 dark:text-gray-300">Кол.</th>
                    <th className="text-left px-2 py-2 font-medium text-gray-600 dark:text-gray-300">Сотрудник</th>
                  </tr>
                </thead>
                <tbody>
                  {foundAssets.map((a) => (
                    <tr key={a.id} className="border-t border-gray-100 dark:border-gray-700">
                      <td className="px-2 py-1.5">
                        <input
                          type="checkbox"
                          checked={selectedIds.has(a.id)}
                          onChange={() => toggleAsset(a.id)}
                          className="w-4 h-4 rounded"
                        />
                      </td>
                      <td className="px-2 py-1.5 text-gray-900 dark:text-gray-100">{a.name}</td>
                      <td className="px-2 py-1.5 text-gray-700 dark:text-gray-300">{a.inventory_number}</td>
                      <td className="px-2 py-1.5 text-gray-700 dark:text-gray-300">{a.model || '—'}</td>
                      <td className="px-2 py-1.5 text-gray-700 dark:text-gray-300">{a.serial_number || '—'}</td>
                      <td className="px-2 py-1.5 text-gray-700 dark:text-gray-300">{a.quantity || 1}</td>
                      <td className="px-2 py-1.5 text-gray-700 dark:text-gray-300">{a.employee_name || a.responsible_person || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Сотрудник — получатель имущества
          </label>
          <select
            value={selectedEmployee ?? ''}
            onChange={(e) => setSelectedEmployee(e.target.value ? Number(e.target.value) : null)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
          >
            <option value="">— Выберите сотрудника —</option>
            {employees.map((e) => (
              <option key={e.id} value={e.id}>
                {e.full_name} — {e.position || '—'} ({e.department_name || '—'})
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={createAct}
          disabled={creating || selectedIds.size === 0 || !selectedEmployee}
          className={`w-full py-3 px-4 rounded-lg text-white font-medium transition flex items-center justify-center gap-2 ${
            creating || selectedIds.size === 0 || !selectedEmployee
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {creating ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Формирование акта...
            </span>
          ) : (
            <><FileText className="w-5 h-5" /> Сформировать акт передачи (Excel)</>
          )}
        </button>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
          После подписания акта сотрудник будет автоматически проставлен в данных переданных активов,
          а в историю передач добавится запись.
        </p>
      </div>

      {/* Список актов */}
      <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
        <Archive className="w-4 h-4" /> Сформированные акты ({acts.length})
      </h3>

      {loadingActs ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
        </div>
      ) : acts.length === 0 ? (
        <p className="text-center text-gray-500 dark:text-gray-400 py-8">Актов пока нет</p>
      ) : (
        <div className="space-y-3">
          {acts.map((act) => (
            <div key={act.id} className={`bg-white dark:bg-gray-800 rounded-lg shadow p-4 ${act.signed ? 'border-l-4 border-green-500' : 'border-l-4 border-yellow-500'}`}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-900 dark:text-gray-100">{act.act_number}</span>
                    {act.signed ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">
                        <CheckCircle2 className="w-3 h-3" /> Подписан
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300">
                        Не подписан
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                    Получатель: <span className="font-medium">{act.employee_name || '—'}</span>
                    {act.employee_position ? `, ${act.employee_position}` : ''}
                    {act.room_name ? ` · каб. ${act.room_name}` : ''}
                    {act.department_name ? ` · ${act.department_name}` : ''}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {act.act_date ? new Date(act.act_date).toLocaleString('ru-RU') : ''} · {act.asset_count} активов
                  </div>
                  {act.attachments && act.attachments.length > 0 && (
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Скан-копии:{' '}
                      {act.attachments.map((att) => (
                        <a
                          key={att.id}
                          href={attachmentUrl(act, att.id)}
                          target="_blank"
                          rel="noreferrer"
                          className="text-blue-600 hover:underline mr-2"
                        >
                          {att.filename}
                        </a>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex flex-wrap gap-2 items-center">
                  <a
                    href={`/api/admin/transfer-acts/${act.id}/download`}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-1.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition inline-flex items-center gap-1"
                  >
                    <Download className="w-3.5 h-3.5" /> Скачать акт
                  </a>

                  {!act.signed && (
                    <>
                      <button
                        onClick={() => confirmAct(act)}
                        className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition inline-flex items-center gap-1"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" /> Подписать
                      </button>
                      <button
                        onClick={() => archiveAct(act)}
                        className="px-3 py-1.5 text-xs bg-gray-500 text-white rounded hover:bg-gray-600 transition"
                      >
                        Архив
                      </button>
                    </>
                  )}

                  <label
                    className={`px-3 py-1.5 text-xs bg-purple-600 text-white rounded hover:bg-purple-700 transition cursor-pointer inline-flex items-center gap-1 ${
                      uploadingActId === act.id ? 'opacity-50 pointer-events-none' : ''
                    }`}
                  >
                    <Upload className="w-3.5 h-3.5" /> Скан-копия расписки
                    <input
                      type="file"
                      accept=".pdf,.jpg,.jpeg,.png,.gif,.webp,.bmp,.tif,.tiff"
                      multiple
                      className="hidden"
                      onChange={(e) => {
                        uploadScan(act, e.target.files);
                        e.target.value = '';
                      }}
                    />
                  </label>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};