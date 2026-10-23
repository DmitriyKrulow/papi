// frontend/src/components/navigation/Sidebar.tsx
import { useState, useEffect, useCallback } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useTheme } from '../../hooks/useTheme';
import {
  LayoutDashboard, Package, ClipboardList, Tag, BarChart3,
  Settings, ChevronLeft, ChevronRight, LogOut, UserCog,
  Shield, Bell, Search, FileText, Wrench, Calendar,
  MoreHorizontal, X, Printer, TrendingUp, FileCheck, Scale,
} from 'lucide-react';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
  adminOnly?: boolean;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isAuthenticated, isAdmin } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  // Автоматическое сворачивание на маленьких экранах
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        setCollapsed(true);
      }
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const isActive = useCallback((path: string) => {
    if (path === '/dashboard') return location.pathname === path;
    return location.pathname.startsWith(path);
  }, [location.pathname]);

  const navSections: NavSection[] = [
    {
      title: 'Основное',
      items: [
        { path: '/dashboard', label: 'Дашборд', icon: <LayoutDashboard className="w-5 h-5" /> },
        { path: '/assets', label: 'Активы', icon: <Package className="w-5 h-5" /> },
        { path: '/inventory', label: 'Инвентаризация', icon: <ClipboardList className="w-5 h-5" /> },
        { path: '/marking', label: 'Маркировка', icon: <Tag className="w-5 h-5" /> },
        { path: '/reports', label: 'Отчёты', icon: <BarChart3 className="w-5 h-5" /> },
        { path: '/repairs', label: 'Ремонты', icon: <Wrench className="w-5 h-5" /> },
        { path: '/schedule', label: 'Расписание', icon: <Calendar className="w-5 h-5" /> },
        { path: '/notifications', label: 'Уведомления', icon: <Bell className="w-5 h-5" /> },
      ],
    },
    {
      title: 'Управление',
      items: isAdmin ? [
        { path: '/admin', label: 'Панель управления', icon: <Settings className="w-5 h-5" />, adminOnly: true },
        { path: '/audit', label: 'Журнал аудита', icon: <FileText className="w-5 h-5" />, adminOnly: true },
        { path: '/analytics', label: 'Аналитика', icon: <TrendingUp className="w-5 h-5" />, adminOnly: true },
        { path: '/disposal', label: 'Списание', icon: <X className="w-5 h-5" />, adminOnly: true },
        { path: '/regulatory', label: 'Документы', icon: <Scale className="w-5 h-5" />, adminOnly: true },
        { path: '/reconciliation', label: 'Сверка', icon: <FileCheck className="w-5 h-5" />, adminOnly: true },
        { path: '/room-inventory-print', label: 'Печать описи', icon: <Printer className="w-5 h-5" />, adminOnly: true },
      ] : [],
    },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
    setMobileOpen(false);
  };

  const renderNavItem = (item: NavItem) => {
    if (item.adminOnly && !isAdmin) return null;
    
    return (
      <Link
        key={item.path}
        to={item.path}
        onClick={() => setMobileOpen(false)}
        className={`sidebar-item ${isActive(item.path) ? 'active' : ''}`}
        title={collapsed ? item.label : undefined}
      >
        <span className="icon text-brand-500 dark:text-accent-400">{item.icon}</span>
        <span className="label">{item.label}</span>
      </Link>
    );
  };

  // Для collapsed режима — только иконки в одну колонку
  if (collapsed) {
    return (
      <>
        {/* Overlay для мобильных */}
        {mobileOpen && (
          <div
            className="fixed inset-0 bg-black/40 z-30 lg:hidden"
            onClick={() => setMobileOpen(false)}
          />
        )}
        
        <aside className={`
          fixed inset-y-0 left-0 z-40 flex flex-col
          bg-white dark:bg-graphite-900 border-r border-gray-100 dark:border-graphite-800
          transition-all duration-300 ease-in-out
          ${mobileOpen ? 'sidebar-expanded shadow-2xl' : 'sidebar-collapsed'}
          lg:shadow-none
        `}>
          {/* Header */}
          <div className="flex items-center justify-between p-3 border-b border-gray-100 dark:border-graphite-800">
            <Link to="/dashboard" className="flex items-center gap-2">
              <span className="text-xl">🏗️</span>
              {!collapsed && <span className="font-bold text-brand-700 dark:text-accent-400">PAPI</span>}
            </Link>
            <button
              onClick={() => setMobileOpen(false)}
              className="lg:hidden p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-graphite-800 transition-colors"
            >
              <X className="w-4 h-4 text-gray-500" />
            </button>
          </div>

          {/* Nav items */}
          <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
            {navSections.map(section => (
              <div key={section.title}>
                {!collapsed && (
                  <div className="px-3 py-2 text-[10px] font-semibold text-gray-400 dark:text-graphite-600 uppercase tracking-wider">
                    {section.title}
                  </div>
                )}
                <div className="space-y-0.5">
                  {section.items.map(renderNavItem)}
                </div>
              </div>
            ))}
          </nav>

          {/* Footer actions */}
          <div className="p-2 border-t border-gray-100 dark:border-graphite-800 space-y-0.5">
            <button
              onClick={toggleTheme}
              className="sidebar-item"
              title={theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
            >
              {theme === 'dark' ? (
                <span className="icon text-yellow-500">☀️</span>
              ) : (
                <span className="icon text-gray-500">🌙</span>
              )}
              <span className="label">{theme === 'dark' ? 'Светлая' : 'Тёмная'}</span>
            </button>

            {isAuthenticated && (
              <Link
                to="/profile"
                className={`sidebar-item ${isActive('/profile') ? 'active' : ''}`}
                onClick={() => setMobileOpen(false)}
              >
                <span className="icon text-brand-500 dark:text-accent-400"><UserCog className="w-5 h-5" /></span>
                <span className="label">{user?.username || 'Профиль'}</span>
              </Link>
            )}

            {isAuthenticated && (
              <button
                onClick={handleLogout}
                className="sidebar-item text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 dark:text-red-400"
              >
                <span className="icon"><LogOut className="w-5 h-5" /></span>
                <span className="label">Выйти</span>
              </button>
            )}
          </div>

          {/* Toggle button */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="absolute -right-3 top-14 w-6 h-6 rounded-full bg-white dark:bg-graphite-800 border border-gray-200 dark:border-graphite-700 shadow-sm flex items-center justify-center hover:border-accent-400 transition-colors z-50"
            title={collapsed ? 'Развернуть' : 'Свернуть'}
          >
            {collapsed ? (
              <ChevronRight className="w-3 h-3 text-gray-500 dark:text-gray-400" />
            ) : (
              <ChevronLeft className="w-3 h-3 text-gray-500 dark:text-gray-400" />
            )}
          </button>
        </aside>
      </>
    );
  }

  // Expanded mode (mobile only — on desktop always collapsed)
  return (
    <>
      {/* Mobile hamburger */}
      <button
        onClick={() => setMobileOpen(true)}
        className="lg:hidden fixed top-3 left-3 z-50 p-2 rounded-lg bg-white dark:bg-graphite-900 shadow-card border border-gray-100 dark:border-graphite-800"
        title="Меню"
      >
        <MoreHorizontal className="w-5 h-5 text-brand-600 dark:text-accent-400" />
      </button>

      {/* Full sidebar for mobile overlay */}
      {mobileOpen && (
        <aside className="sidebar-expanded fixed inset-y-0 left-0 z-40 flex flex-col bg-white dark:bg-graphite-900 border-r border-gray-100 dark:border-graphite-800 shadow-2xl">
          <div className="flex items-center justify-between p-4 border-b border-gray-100 dark:border-graphite-800">
            <Link to="/dashboard" className="flex items-center gap-2" onClick={() => setMobileOpen(false)}>
              <span className="text-xl">🏗️</span>
              <span className="font-bold text-brand-700 dark:text-accent-400">PAPI</span>
            </Link>
            <button onClick={() => setMobileOpen(false)} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-graphite-800">
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          <nav className="flex-1 overflow-y-auto p-3 space-y-4">
            {navSections.map(section => (
              <div key={section.title}>
                <div className="px-2 py-1.5 text-xs font-semibold text-gray-400 dark:text-graphite-600 uppercase tracking-wider">
                  {section.title}
                </div>
                <div className="space-y-0.5">
                  {section.items.map(renderNavItem)}
                </div>
              </div>
            ))}
          </nav>

          <div className="p-3 border-t border-gray-100 dark:border-graphite-800 space-y-0.5">
            <button
              onClick={toggleTheme}
              className="sidebar-item"
            >
              {theme === 'dark' ? (
                <span className="icon text-yellow-500">☀️</span>
              ) : (
                <span className="icon text-gray-500">🌙</span>
              )}
              <span className="label">{theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}</span>
            </button>

            {isAuthenticated && (
              <Link to="/profile" className="sidebar-item" onClick={() => setMobileOpen(false)}>
                <span className="icon text-brand-500 dark:text-accent-400"><UserCog className="w-5 h-5" /></span>
                <span className="label">{user?.username || 'Профиль'}</span>
              </Link>
            )}

            {isAuthenticated && (
              <button
                onClick={handleLogout}
                className="sidebar-item text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
              >
                <span className="icon"><LogOut className="w-5 h-5" /></span>
                <span className="label">Выйти</span>
              </button>
            )}
          </div>
        </aside>
      )}
    </>
  );
};

export default Sidebar;
