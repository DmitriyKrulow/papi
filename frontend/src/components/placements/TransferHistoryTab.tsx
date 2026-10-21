// frontend/src/components/placements/TransferHistoryTab.tsx
import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import { useAuth } from '../../hooks/useAuth';
import { History } from 'lucide-react';

interface HistoryRow {
  id: number;
  asset_id: number;
  asset_name: string;
  inventory_number: string;
  prev_employee_id: number | null;
  prev_employee_name: string | null;
  new_employee_id: number | null;
  new_employee_name: string | null;
  source: string;
  source_id: number | null;
  source_ref: string | null;
  transfer_date: string | null;
  created_by: string | null;
}

const api = (path: string, init?: RequestInit, token?: string | null) =>
  fetch(path, {
    ...init,
    headers: {
      ...(init?.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

const sourceLabel = (source: string): string => {
  if (source === 'inventory_print') return 'Описью';
  if (source === 'transfer_act') return 'Актом передачи';
  return source;
};

export const TransferHistoryTab: React.FC<{ token?: string | null }> = ({ token }) => {
  const { token: authToken } = useAuth();
  const effectiveToken = token ?? authToken;

  const [rows, setRows] = useState<HistoryRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [loadedAll, setLoadedAll] = useState(false);

  const loadHistory = useCallback(async () => {
    if (!effectiveToken) return;
    setLoading(true);
    try {
      let query = '';
      if (search.trim()) {
        const s = search.trim();
        // Пытаемся найти актив по инв. номеру/названию через API списка, но для истории
        // достаточно локальной фильтрации по полученным строкам.
        void s;
      }
      const res = await api(`/api/admin/transfer-acts/history?limit=2000${query}`, {}, effectiveToken);
      if (res.ok) {
        setRows(await res.json());
      } else {
        toast.error('Ошибка загрузки истории');
      }
    } catch (e: any) {
      toast.error(e.message || 'Ошибка соединения');
    } finally {
      setLoading(false);
      setLoadedAll(true);
    }
  }, [effectiveToken]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const q = search.trim().toLowerCase();
  const filtered = q
    ? rows.filter((r) =>
        [r.asset_name, r.inventory_number, r.new_employee_name, r.prev_employee_name, r.source_ref]
          .filter(Boolean)
          .some((v) => String(v).toLowerCase().includes(q)),
      )
    : rows;

  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
        <History className="w-5 h-5" />
        История передачи активов (описи и акты)
      </h2>

      <div className="mb-4">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Поиск: актив, инв. №, сотрудник..."
          className="w-full max-w-md px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {loading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
        </div>
      ) : filtered.length === 0 ? (
        <p className="text-center text-gray-500 dark:text-gray-400 py-8">
          {loadedAll ? 'Записей о передаче пока нет' : 'Загрузка...'}
        </p>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Дата</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Актив</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Передан от</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Передан кому</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Основание</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300">Пользователь</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr key={r.id} className="border-b border-gray-100 dark:border-gray-700">
                  <td className="px-4 py-3 text-gray-700 dark:text-gray-300 whitespace-nowrap">
                    {r.transfer_date ? new Date(r.transfer_date).toLocaleString('ru-RU') : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-gray-900 dark:text-gray-100 font-medium">{r.asset_name || `Актив #${r.asset_id}`}</div>
                    {r.inventory_number && (
                      <div className="text-xs text-gray-500">{r.inventory_number}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                    {r.prev_employee_name || '—'}
                  </td>
                  <td className="px-4 py-3 text-gray-900 dark:text-gray-100 font-medium">
                    {r.new_employee_name || '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                      r.source === 'transfer_act'
                        ? 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300'
                        : 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                    }`}>
                      {sourceLabel(r.source)} {r.source_ref ? `· ${r.source_ref}` : ''}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{r.created_by || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {filtered.length > 0 && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
          Показано записей: {filtered.length}
        </p>
      )}
    </div>
  );
};