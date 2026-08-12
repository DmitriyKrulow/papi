// frontend/src/pages/NotificationsPage.tsx
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { notificationsApi, type NotificationItem } from '../api/notifications';
import {
  Bell,
  Check,
  Trash2,
  Filter,
  Clock,
  X,
  RefreshCw,
  Archive,
  AlertCircle,
} from 'lucide-react';

const NOTIFICATION_TYPE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  warranty: { bg: 'bg-yellow-50 dark:bg-yellow-900/20', text: 'text-yellow-800 dark:text-yellow-200', border: 'border-yellow-200 dark:border-yellow-800' },
  maintenance: { bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-800 dark:text-blue-200', border: 'border-blue-200 dark:border-blue-800' },
  repair_overdue: { bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-800 dark:text-red-200', border: 'border-red-200 dark:border-red-800' },
  inventory: { bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-800 dark:text-green-200', border: 'border-green-200 dark:border-green-800' },
  status_change: { bg: 'bg-purple-50 dark:bg-purple-900/20', text: 'text-purple-800 dark:text-purple-200', border: 'border-purple-200 dark:border-purple-800' },
  manual: { bg: 'bg-gray-50 dark:bg-gray-900/20', text: 'text-gray-800 dark:text-gray-200', border: 'border-gray-200 dark:border-gray-800' },
  general: { bg: 'bg-gray-50 dark:bg-gray-900/20', text: 'text-gray-800 dark:text-gray-200', border: 'border-gray-200 dark:border-gray-800' },
};

const NotificationsPage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>('');
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);
  const [page, setPage] = useState(1);
  const limit = 50;

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const [data, countData] = await Promise.all([
        notificationsApi.list({
          limit,
          offset: (page - 1) * limit,
          type: filterType || undefined,
          unread_only: showUnreadOnly,
        }),
        notificationsApi.getUnreadCount(),
      ]);
      setNotifications(data);
      setUnreadCount(countData.count || 0);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  }, [page, filterType, showUnreadOnly]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchNotifications();
    }
  }, [isAuthenticated, fetchNotifications]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  const handleMarkAsRead = async (id: number) => {
    try {
      await notificationsApi.markAsRead(id);
      setNotifications(prev =>
        prev.map(n => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Failed to mark as read:', err);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificationsApi.markAllAsRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to mark all as read:', err);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await notificationsApi.delete(id);
      setNotifications(prev => prev.filter(n => n.id !== id));
      setUnreadCount(prev => {
        const notif = notifications.find(n => n.id === id);
        return notif && !notif.is_read ? Math.max(0, prev - 1) : prev;
      });
    } catch (err) {
      console.error('Failed to delete notification:', err);
    }
  };

  const handleDeleteAllRead = async () => {
    try {
      await notificationsApi.deleteAllRead();
      setNotifications(prev => prev.filter(n => !n.is_read));
    } catch (err) {
      console.error('Failed to delete read notifications:', err);
    }
  };

  const handleGenerateAuto = async () => {
    try {
      await notificationsApi.generateAuto();
      fetchNotifications();
    } catch (err) {
      console.error('Failed to generate auto notifications:', err);
    }
  };

  const unreadCountTotal = notifications.filter(n => !n.is_read).length;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-4">
          <div>
            <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-1">
              <Bell className="w-8 h-8 inline-block mr-2" />
              Уведомления
            </h1>
            <p className="text-gray-500 dark:text-gray-400">
              {unreadCount > 0
                ? `У вас ${unreadCount} непрочитанных уведомлений`
                : 'Все уведомления прочитаны'}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleGenerateAuto}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm"
            >
              <RefreshCw className="w-4 h-4" />
              Проверить
            </button>
            <button
              onClick={fetchNotifications}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition text-sm"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Обновить
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-3 gap-3 sm:gap-4 mb-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-1">
              <Bell className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <span className="text-xs text-gray-500 dark:text-gray-400">Всего</span>
            </div>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {notifications.length}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-1">
              <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
              <span className="text-xs text-gray-500 dark:text-gray-400">Непрочитанные</span>
            </div>
            <p className="text-2xl font-bold text-red-600 dark:text-red-400">
              {unreadCountTotal}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-1">
              <Check className="w-4 h-4 text-green-600 dark:text-green-400" />
              <span className="text-xs text-gray-500 dark:text-gray-400">Прочитанные</span>
            </div>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
              {notifications.length - unreadCountTotal}
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow mb-6 border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex flex-wrap gap-3 items-center">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-600 dark:text-gray-400">Фильтр:</span>
            </div>
            <select
              value={filterType}
              onChange={(e) => { setFilterType(e.target.value); setPage(1); }}
              className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-sm text-gray-900 dark:text-gray-100"
            >
              <option value="">Все типы</option>
              <option value="warranty">🔔 Гарантия</option>
              <option value="maintenance">🔧 Обслуживание</option>
              <option value="repair_overdue">🛠️ Просроченный ремонт</option>
              <option value="inventory">📋 Инвентаризация</option>
              <option value="status_change">🔄 Смена статуса</option>
            </select>
            <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
              <input
                type="checkbox"
                checked={showUnreadOnly}
                onChange={(e) => { setShowUnreadOnly(e.target.checked); setPage(1); }}
                className="rounded border-gray-300 dark:border-gray-600"
              />
              Только непрочитанные
            </label>
            <div className="flex-1" />
            <button
              onClick={handleMarkAllAsRead}
              className="px-3 py-1.5 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition"
            >
              Прочитать все
            </button>
            <button
              onClick={handleDeleteAllRead}
              className="px-3 py-1.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition flex items-center gap-1"
            >
              <Trash2 className="w-3 h-3" />
              Удалить прочитанные
            </button>
          </div>
        </div>

        {/* Notifications List */}
        <div className="space-y-3">
          {loading ? (
            <div className="flex justify-center items-center py-16">
              <div className="text-center">
                <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-3" />
                <p className="text-gray-500 dark:text-gray-400">Загрузка уведомлений...</p>
              </div>
            </div>
          ) : notifications.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-100 dark:border-gray-700 p-12 text-center">
              <Bell className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                Уведомлений нет
              </h3>
              <p className="text-gray-500 dark:text-gray-400">
                {showUnreadOnly
                  ? 'Нет непрочитанных уведомлений'
                  : 'У вас пока нет уведомлений'}
              </p>
            </div>
          ) : (
            notifications.map((notif) => {
              const colors = NOTIFICATION_TYPE_COLORS[notif.type] || NOTIFICATION_TYPE_COLORS.general;
              return (
                <div
                  key={notif.id}
                  className={`bg-white dark:bg-gray-800 rounded-lg shadow border transition ${
                    notif.is_read
                      ? 'border-gray-100 dark:border-gray-700'
                      : `${colors.border} ring-1 ring-offset-1 dark:ring-offset-gray-900 ${colors.text.replace('text-', 'ring-')}`
                  } ${!notif.is_read ? 'hover:shadow-md' : ''}`}
                >
                  <div className="p-4">
                    <div className="flex items-start gap-3">
                      {/* Icon */}
                      <div className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center text-lg ${colors.bg}`}>
                        {notif.type_icon}
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <h3 className={`text-sm font-semibold truncate ${
                              notif.is_read ? 'text-gray-700 dark:text-gray-300' : 'text-gray-900 dark:text-gray-100'
                            }`}>
                              {notif.title}
                            </h3>
                            {notif.entity_name && (
                              <p className="text-xs text-blue-600 dark:text-blue-400 mt-0.5">
                                {notif.entity_name}
                              </p>
                            )}
                            <p className={`text-sm mt-1 ${
                              notif.is_read ? 'text-gray-500 dark:text-gray-400' : 'text-gray-700 dark:text-gray-300'
                            }`}>
                              {notif.message}
                            </p>
                          </div>
                          {/* Actions */}
                          <div className="flex items-center gap-1 flex-shrink-0">
                            {!notif.is_read && (
                              <button
                                onClick={() => handleMarkAsRead(notif.id)}
                                className="p-1.5 text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition"
                                title="Отметить как прочитанное"
                              >
                                <Check className="w-4 h-4" />
                              </button>
                            )}
                            <button
                              onClick={() => handleDelete(notif.id)}
                              className="p-1.5 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition"
                              title="Удалить"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                        {/* Footer */}
                        <div className="flex items-center gap-2 mt-2">
                          <span className={`inline-block px-2 py-0.5 text-[10px] font-medium rounded ${colors.bg} ${colors.text}`}>
                            {notif.type_label}
                          </span>
                          <div className="flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500">
                            <Clock className="w-3 h-3" />
                            <span>{new Date(notif.created_at).toLocaleString('ru-RU')}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Pagination */}
        {notifications.length > 0 && (
          <div className="flex items-center justify-between mt-6">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Показано {notifications.length} из {notifications.length}
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Назад
              </button>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Страница {page}
              </span>
              <button
                onClick={() => setPage(p => p + 1)}
                className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Вперёд
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default NotificationsPage;
