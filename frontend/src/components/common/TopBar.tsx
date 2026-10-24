// frontend/src/components/common/TopBar.tsx
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useTheme } from '../../hooks/useTheme';
import { useNavSections } from '../navigation/navItems';
import { Sun, Moon, UserCog, LogOut, Menu, X, Bell, Search } from 'lucide-react';
import NotificationDropdown from '../notifications/NotificationDropdown';

const TopBar = () => {
  const navigate = useNavigate();
  const { user, logout, isAuthenticated, isAdmin } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navSections = useNavSections(isAdmin);

  const handleLogout = () => {
    logout();
    navigate('/login');
    setMobileMenuOpen(false);
  };

  return (
    <header className="sticky top-0 z-20 bg-white/80 dark:bg-graphite-900/80 backdrop-blur-md border-b border-gray-100 dark:border-graphite-800">
      <div className="flex items-center justify-between h-12 px-4">
        {/* Left: Logo */}
        <Link to="/dashboard" className="flex items-center gap-2 flex-shrink-0">
          <span className="text-lg">🏗️</span>
          <span className="hidden sm:block font-bold text-brand-600 dark:text-accent-400 text-sm">PAPI</span>
        </Link>

        {/* Center: Search (desktop) */}
        <div className="hidden md:flex flex-1 max-w-md mx-4">
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Поиск активов, помещений..."
              className="w-full pl-9 pr-3 py-1.5 text-sm border border-gray-200 dark:border-graphite-700 rounded-lg bg-gray-50 dark:bg-graphite-800 text-gray-900 dark:text-graphite-100 focus:outline-none focus:ring-1 focus:ring-accent-400/50 transition-all placeholder:text-gray-400"
            />
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-1">
          {isAuthenticated && <NotificationDropdown />}

          <button
            onClick={toggleTheme}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-graphite-800 transition-colors"
            title={theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-yellow-500" />
            ) : (
              <Moon className="w-4 h-4 text-gray-500" />
            )}
          </button>

          {isAuthenticated && user && (
            <Link 
              to="/profile" 
              className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-graphite-800 transition-colors"
              title={user.username}
            >
              <UserCog className="w-4 h-4 text-brand-500 dark:text-accent-400" />
            </Link>
          )}

          {isAuthenticated && (
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              title="Выйти"
            >
              <LogOut className="w-4 h-4 text-gray-400 hover:text-red-500 transition-colors" />
            </button>
          )}

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-graphite-800 transition-colors"
          >
            {mobileMenuOpen ? (
              <X className="w-5 h-5 text-gray-500" />
            ) : (
              <Menu className="w-5 h-5 text-gray-500" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-gray-100 dark:border-graphite-800 bg-white dark:bg-graphite-900 py-2 px-3 space-y-4 max-h-[80vh] overflow-y-auto">
          {/* Search (mobile) */}
          <div className="md:hidden">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Поиск..."
                className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-accent-400/50 placeholder:text-gray-400"
              />
            </div>
          </div>
          
          {/* User info */}
          {isAuthenticated && user && (
            <div className="px-2 py-1.5 text-sm text-gray-500 dark:text-gray-400 flex items-center gap-2">
              <UserCog className="w-4 h-4" />
              {user.username}
            </div>
          )}
          
          {/* Navigation sections */}
          {isAuthenticated && (
            <>
              {navSections.map(section => (
                <div key={section.title}>
                  <div className="px-2 py-1 text-xs font-semibold text-gray-400 dark:text-gray-600 uppercase tracking-wider">
                    {section.title}
                  </div>
                  <div className="space-y-0.5">
                    {section.items.map(item => (
                      <Link
                        key={item.path}
                        to={item.path}
                        onClick={() => setMobileMenuOpen(false)}
                        className="block px-3 py-2 rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-gray-700 dark:text-gray-300 flex items-center gap-2"
                      >
                        <span className="flex-shrink-0">{item.icon}</span>
                        <span>{item.label}</span>
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
            </>
          )}

          {/* Logout */}
          {isAuthenticated && (
            <button
              onClick={handleLogout}
              className="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors text-red-500 flex items-center gap-2"
            >
              <LogOut className="w-4 h-4" />
              Выйти
            </button>
          )}
        </div>
      )}
    </header>
  );
};

export default TopBar;
