// frontend/src/components/navigation/Sidebar.tsx
import { useState, useEffect, useCallback } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useTheme } from '../../hooks/useTheme';
import { useNavSections, type NavItem } from './navItems';
import {
  ChevronLeft, ChevronRight, LogOut, UserCog,
} from 'lucide-react';

const MOBILE_BREAKPOINT = 1024;

const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isAuthenticated, isAdmin } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [collapsed, setCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(
    typeof window !== 'undefined' ? window.innerWidth < MOBILE_BREAKPOINT : false
  );

  // На мобильных (<1024px) боковая панель не показывается — меню в TopBar
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const isActive = useCallback((path: string) => {
    if (path === '/dashboard') return location.pathname === path;
    return location.pathname.startsWith(path);
  }, [location.pathname]);

  const navSections = useNavSections(isAdmin);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // На мобильных навигация живёт в выпадающем меню TopBar
  if (isMobile) return null;

  const showLabels = !collapsed;
  const widthClass = showLabels ? 'w-[224px] min-w-[224px]' : 'w-[64px] min-w-[64px]';

  const renderNavItem = (item: NavItem) => {
    if (item.adminOnly && !isAdmin) return null;

    return (
      <Link
        key={item.path}
        to={item.path}
        className={`sidebar-item ${isActive(item.path) ? 'active' : ''}`}
        title={showLabels ? item.label : undefined}
      >
        <span className="icon text-brand-500 dark:text-accent-400">{item.icon}</span>
        {showLabels && <span className="label">{item.label}</span>}
      </Link>
    );
  };

  return (
    <aside className={`
      relative flex flex-col flex-shrink-0
      sticky top-0 z-30 h-screen
      bg-white dark:bg-graphite-900 border-r border-gray-100 dark:border-graphite-800
      transition-[width,min-width] duration-300 ease-in-out
      ${widthClass}
    `}>
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-100 dark:border-graphite-800 h-12">
        <Link to="/dashboard" className="flex items-center gap-2">
          <span className="text-xl">🏗️</span>
          {showLabels && <span className="font-bold text-brand-700 dark:text-accent-400">PAPI</span>}
        </Link>
      </div>

      {/* Nav items */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden p-2 space-y-1 sidebar-nav">
        {navSections.map(section => {
          const items = section.items.filter(i => !i.adminOnly || isAdmin);
          if (items.length === 0) return null;
          return (
            <div key={section.title}>
              {showLabels && (
                <div className="px-3 py-1.5 text-[10px] font-semibold text-gray-400 dark:text-graphite-600 uppercase tracking-wider">
                  {section.title}
                </div>
              )}
              <div className="space-y-0.5">
                {items.map(renderNavItem)}
              </div>
            </div>
          );
        })}
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
          {showLabels && <span className="label">{theme === 'dark' ? 'Светлая' : 'Тёмная'}</span>}
        </button>

        {isAuthenticated && (
          <Link
            to="/profile"
            className={`sidebar-item ${isActive('/profile') ? 'active' : ''}`}
            title={showLabels ? undefined : (user?.username || 'Профиль')}
          >
            <span className="icon text-brand-500 dark:text-accent-400"><UserCog className="w-5 h-5" /></span>
            {showLabels && <span className="label">{user?.username || 'Профиль'}</span>}
          </Link>
        )}

        {isAuthenticated && (
          <button
            onClick={handleLogout}
            className="sidebar-item text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 dark:text-red-400"
            title={showLabels ? undefined : 'Выйти'}
          >
            <span className="icon"><LogOut className="w-5 h-5" /></span>
            {showLabels && <span className="label">Выйти</span>}
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
  );
};

export default Sidebar;
