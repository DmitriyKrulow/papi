// frontend/src/pages/RfidKeysPage.tsx
import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';

interface RfidKey {
  id: number;
  name: string;
  key_prefix: string;
  is_active: boolean;
  created_by?: number;
  created_at?: string;
  last_used_at?: string;
}

interface RfidStats {
  total_keys: number;
  active_keys: number;
  recently_used: number;
  inactive_keys: number;
}

const RfidKeysPage: React.FC = () => {
  const [keys, setKeys] = useState<RfidKey[]>([]);
  const [stats, setStats] = useState<RfidStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const fetchKeys = async () => {
    try {
      const token = localStorage.getItem('token');
      const [keysRes, statsRes] = await Promise.all([
        fetch('/api/admin/rfid-keys', { headers: { 'Authorization': `Bearer ${token}` } }),
        fetch('/api/admin/rfid-keys/stats', { headers: { 'Authorization': `Bearer ${token}` } }),
      ]);
      
      if (keysRes.ok) {
        const data = await keysRes.json();
        setKeys(data.keys || []);
      }
      if (statsRes.ok) {
        const data = await statsRes.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch RFID keys:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) {
      toast.error('Введите название ключа');
      return;
    }
    
    try {
      setCreating(true);
      const token = localStorage.getItem('token');
      const response = await fetch(
        `/api/admin/rfid-keys?name=${encodeURIComponent(newKeyName)}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setCreatedKey(data.api_key);
        setNewKeyName('');
        toast.success('API-ключ создан! СОХРАНИТЕ ЕГО СЕЙЧАС!');
        fetchKeys();
      } else {
        const err = await response.json();
        toast.error(err.detail || 'Ошибка создания ключа');
      }
    } catch (err) {
      toast.error('Ошибка соединения');
    } finally {
      setCreating(false);
    }
  };

  const handleDeactivate = async (keyId: number) => {
    if (!confirm('Деактивировать этот ключ? Сканер перестанет работать.')) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/rfid-keys/${keyId}/deactivate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        toast.success('Ключ деактивирован');
        fetchKeys();
      } else {
        toast.error('Ошибка деактивации');
      }
    } catch (err) {
      toast.error('Ошибка соединения');
    }
  };

  const handleDelete = async (keyId: number) => {
    if (!confirm('Удалить этот ключ навсегда? Это действие нельзя отменить.')) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/rfid-keys/${keyId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        toast.success('Ключ удалён');
        fetchKeys();
      } else {
        toast.error('Ошибка удаления');
      }
    } catch (err) {
      toast.error('Ошибка соединения');
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast.success('Скопировано в буфер обмена');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Не удалось скопировать');
    }
  };

  if (loading) {
    return <div className="text-center py-8 text-gray-500">Загрузка...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="text-2xl font-bold text-blue-900 dark:text-blue-300">{stats.total_keys}</div>
            <div className="text-sm text-blue-700 dark:text-blue-400">Всего ключей</div>
          </div>
          <div className="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-900 dark:text-green-300">{stats.active_keys}</div>
            <div className="text-sm text-green-700 dark:text-green-400">Активных</div>
          </div>
          <div className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
            <div className="text-2xl font-bold text-yellow-900 dark:text-yellow-300">{stats.recently_used}</div>
            <div className="text-sm text-yellow-700 dark:text-yellow-400">Использовались 24ч</div>
          </div>
          <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div className="text-2xl font-bold text-red-900 dark:text-red-300">{stats.inactive_keys}</div>
            <div className="text-sm text-red-700 dark:text-red-400">Неактивных</div>
          </div>
        </div>
      )}

      {/* Create Key */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 border border-gray-100 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">
          ➕ Создать API-ключ для RFID-сканера
        </h2>
        
        <div className="flex gap-3 mb-4">
          <input
            type="text"
            placeholder="Название (напр. 'Сканер цех 1')"
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
          <button
            onClick={handleCreateKey}
            disabled={creating}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm disabled:opacity-50"
          >
            {creating ? 'Создание...' : 'Создать ключ'}
          </button>
        </div>

        {/* Created Key Display */}
        {createdKey && (
          <div className="bg-red-50 dark:bg-red-900/30 border-2 border-red-300 dark:border-red-700 rounded-lg p-4">
            <h3 className="font-bold text-red-900 dark:text-red-300 mb-2">
              ⚠️ API-КЛЮЧ СОЗДАН! СОХРАНИТЕ ЕГО СЕЙЧАС!
            </h3>
            <p className="text-sm text-red-700 dark:text-red-400 mb-3">
              Этот ключ будет показан ТОЛЬКО ОДИН РАЗ. После закрытия окна восстановить его невозможно.
            </p>
            <div className="flex gap-2 items-center">
              <code className="flex-1 bg-gray-900 text-green-400 px-3 py-2 rounded text-sm font-mono break-all">
                {createdKey}
              </code>
              <button
                onClick={() => copyToClipboard(createdKey)}
                className="bg-gray-700 text-white px-3 py-2 rounded hover:bg-gray-600 transition text-sm whitespace-nowrap"
              >
                {copied ? '✅ Скопировано' : '📋 Копировать'}
              </button>
            </div>
            <button
              onClick={() => { setCreatedKey(null); fetchKeys(); }}
              className="mt-3 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition text-sm"
            >
              Понял, сохраняю
            </button>
          </div>
        )}
      </div>

      {/* Keys List */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 border border-gray-100 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">
          📡 Список API-ключей
        </h2>

        {keys.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            API-ключей пока нет. Создайте первый ключ выше.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Название</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Префикс ключа</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Статус</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Создан</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Последнее использование</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Действия</th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {keys.map((key) => (
                  <tr key={key.id} className="hover:bg-gray-50 dark:hover:bg-gray-750 transition">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{key.id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">{key.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500 dark:text-gray-400">
                      {key.key_prefix}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        key.is_active 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' 
                          : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
                      }`}>
                        {key.is_active ? 'Активен' : 'Неактивен'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {key.created_at ? new Date(key.created_at).toLocaleDateString('ru-RU') : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {key.last_used_at ? new Date(key.last_used_at).toLocaleString('ru-RU') : 'Никогда'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                      <div className="flex justify-end gap-2">
                        {key.is_active ? (
                          <button
                            onClick={() => handleDeactivate(key.id)}
                            className="bg-yellow-600 text-white px-3 py-1 rounded hover:bg-yellow-700 transition"
                          >
                            Деактивировать
                          </button>
                        ) : (
                          <button
                            onClick={() => handleDelete(key.id)}
                            className="bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700 transition"
                          >
                            Удалить
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Instructions */}
      <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 dark:text-blue-300 mb-2">
          ℹ️ Как использовать
        </h3>
        <ul className="text-sm text-blue-800 dark:text-blue-400 space-y-1 list-disc list-inside">
          <li>Создайте API-ключ для каждого RFID-сканера с понятным названием</li>
          <li>Сохраните ключ в приложении Windows-сканера при настройке</li>
          <li>Ключ отправляется в заголовке <code className="bg-gray-200 dark:bg-gray-700 px-1 rounded">X-API-Key</code></li>
          <li>Пример: <code className="bg-gray-200 dark:bg-gray-700 px-1 rounded">X-API-Key: rfid_abc123def456...</code></li>
          <li>Для деактивации ключа нажмите "Деактивировать", для удаления — "Удалить"</li>
        </ul>
      </div>
    </div>
  );
};

export default RfidKeysPage;
