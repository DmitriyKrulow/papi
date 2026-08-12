// frontend/src/components/notifications/NotificationDropdown.tsx
import { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { notificationsApi, type NotificationItem } from '../../api/notifications';
import { useAuth } from '../../hooks/useAuth';
import {
  Bell,
  Check,
  X,
  Trash2,
  Clock,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

interface NotificationDropdownProps {
  onCountChange?: (count: number) => void;
}

const NOTIFICATION_TYPE_COLORS: Record<string, string> = {
  warranty: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200',
  maintenance: 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200',
  repair_overdue: 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200',
  inventory: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200',
  status_change: 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200',
  general: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200',
};

const NotificationDropdown: React.FC<NotificationDropdownProps> = ({ onCountChange }) => {
  const { isAuthenticated } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const fetchUnread = useCallback(async () => {
    // Не делаем запрос если пользователь не авторизован
    if (!isAuthenticated) {
      setUnreadCount(0);
      onCountChange?.(0);
      return;
    }
    
    setLoading(true);
    try {
      const [data, countData] = await Promise.all([
        notificationsApi.list({ limit: 10, unread_only: true }),
        notificationsApi.getUnreadCount(),
      ]);
      setNotifications(data);
      setUnreadCount(countData.count || 0);
      onCountChange?.(countData.count || 0);
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
      // При ошибке (включая 401) не удаляем токен, просто сбрасываем счётчик
      setUnreadCount(0);
      onCountChange?.(0);
    } finally {
      setLoading(false);
    }
  }, [onCountChange, isAuthenticated]);

  // Fetch on mount and when dropdown opens
  useEffect(() => {
    if (isAuthenticated) {
      fetchUnread();
    } else {
      setUnreadCount(0);
    }
  }, [fetchUnread, isAuthenticated]);

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMarkAsRead = async (id: number) => {
    try {
      await notificationsApi.markAsRead(id);
      setNotifications(prev => prev.map(n => (n.id === id ? { ...n, is_read: true } : n)));
      setUnreadCount(prev => Math.max(0, prev - 1));
      onCountChange?.(Math.max(0, unreadCount - 1));
    } catch (err) {
      console.error('Failed to mark as read:', err);
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
      onCountChange?.(Math.max(0, unreadCount - (notifications.find(n => n.id === id)?.is_read ? 0 : 1)));
    } catch (err) {
      console.error('Failed to delete:', err);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificationsApi.markAllAsRead();
      setNotifications([]);
      setUnreadCount(0);
      onCountChange?.(0);
    } catch (err) {
      console.error('Failed to mark all as read:', err);
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"
        title="Уведомления"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center animate-pulse">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 max-h-[80vh] bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden z-50">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                Уведомления
              </h3>
              {unreadCount > 0 && (
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {unreadCount} непрочитанных
                </p>
              )}
            </div>
            <div className="flex items-center gap-1">
              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllAsRead}
                  className="p-1.5 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition"
                  title="Прочитать все"
                >
                  <Check className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Notifications List */}
          <div className="overflow-y-auto max-h-[60vh]">
            {loading ? (
              <div className="flex justify-center items-center py-8">
                <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : notifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <Bell className="w-12 h-12 text-gray-300 dark:text-gray-600 mb-2" />
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Нет непрочитанных уведомлений
                </p>
              </div>
            ) : (
              notifications.map((notif) => (
                <div
                  key={notif.id}
                  className={`p-3 border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition ${
                    !notif.is_read ? 'bg-blue-50/50 dark:bg-blue-900/10' : ''
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-sm ${NOTIFICATION_TYPE_COLORS[notif.type] || NOTIFICATION_TYPE_COLORS.general}`}>
                      {notif.type_icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={`text-xs font-medium truncate ${
                        notif.is_read ? 'text-gray-600 dark:text-gray-400' : 'text-gray-900 dark:text-gray-100'
                      }`}>
                        {notif.title}
                      </p>
                      <p className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">
                        {notif.message}
                      </p>
                      <div className="flex items-center gap-1 mt-1">
                        <span className={`inline-block px-1.5 py-0.5 text-[9px] font-medium rounded ${NOTIFICATION_TYPE_COLORS[notif.type] || NOTIFICATION_TYPE_COLORS.general}`}>
                          {notif.type_label}
                        </span>
                        <span className="text-[9px] text-gray-400 dark:text-gray-500 flex items-center gap-0.5">
                          <Clock className="w-2.5 h-2.5" />
                          {new Date(notif.created_at).toLocaleDateString('ru-RU')}
                        </span>
                      </div>
                    </div>
                    <div className="flex-shrink-0 flex items-center gap-0.5">
                      {!notif.is_read && (
                        <button
                          onClick={() => handleMarkAsRead(notif.id)}
                          className="p-1 text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 rounded transition"
                          title="Прочитать"
                        >
                          <Check className="w-3 h-3" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(notif.id)}
                        className="p-1 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition"
                        title="Удалить"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="p-3 border-t border-gray-200 dark:border-gray-700 text-center">
              <Link
                to="/notifications"
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                onClick={() => setIsOpen(false)}
              >
                Все уведомления →
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationDropdown;
