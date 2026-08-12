// frontend/src/components/common/Navbar.tsx
import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useTheme } from '../../hooks/useTheme';
import { Sun, Moon, Menu, X, ChevronDown, UserCog, Shield } from 'lucide-react';
import NotificationDropdown from '../notifications/NotificationDropdown';

const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isAuthenticated, isAdmin } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [adminMenuOpen, setAdminMenuOpen] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  const navItems = [
    { path: '/dashboard', label: 'Дашборд', icon: '📊' },
    { path: '/assets', label: 'Активы', icon: '📦' },
    { path: '/inventory', label: 'Инвентаризация', icon: '📋' },
    { path: '/marking', label: 'Маркировка', icon: '🏷️' },
    { path: '/reports', label: 'Отчёты', icon: '📈' },
    { path: '/repairs', label: 'Ремонты', icon: '🔧' },
    { path: '/notifications', label: 'Уведомления', icon: '🔔' },
  ];

  const adminItems = [
    { path: '/admin', label: 'Панель управления', icon: '⚙️' },
    { path: '/audit', label: 'Журнал аудита', icon: '📜' },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
    setMobileMenuOpen(false);
    setUserMenuOpen(false);
  };

  const closeMobileMenu = () => {
    setMobileMenuOpen(false);
    setUserMenuOpen(false);
  };

  return (
    <nav className="bg-blue-600 dark:bg-gray-800 text-white dark:text-gray-100 shadow-lg sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to={isAuthenticated ? '/dashboard' : '/'} className="text-xl font-bold flex-shrink-0" onClick={closeMobileMenu}>
            🏗️ PAPI
          </Link>

          {/* Desktop Navigation — responsive: иконки + подписи при широком экране */}
          {isAuthenticated && (
            <div className="hidden lg:flex items-center space-x-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-2 py-2 rounded-lg transition text-sm flex items-center gap-1.5 ${
                    isActive(item.path)
                      ? 'bg-blue-700 dark:bg-gray-700 text-white font-medium'
                      : 'hover:bg-blue-500 dark:hover:bg-gray-700 text-blue-50'
                  }`}
                  title={item.label}
                >
                  <span className="text-base flex-shrink-0">{item.icon}</span>
                  <span className="hidden xl:inline text-sm">{item.label}</span>
                </Link>
              ))}
              
              {isAdmin && (
                <>
                  <div className="w-px h-6 bg-blue-400 dark:bg-gray-600 mx-2" />
                  <div className="relative">
                    <button
                      onClick={() => setAdminMenuOpen(!adminMenuOpen)}
                      className="px-2 py-2 rounded-lg transition text-sm bg-blue-600/50 hover:bg-blue-500 dark:hover:bg-gray-700 text-blue-50 flex items-center gap-1"
                      title="Администрирование"
                    >
                      <Shield className="w-4 h-4 flex-shrink-0" />
                      <span className="hidden xl:inline text-sm">Админ</span>
                      <ChevronDown className={`w-3 h-3 hidden xl:block transition-transform ${adminMenuOpen ? 'rotate-180' : ''}`} />
                    </button>
                    {adminMenuOpen && (
                      <>
                        <div className="fixed inset-0 z-40" onClick={() => setAdminMenuOpen(false)} />
                        <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 z-50 py-2">
                          {adminItems.map((item) => (
                            <Link
                              key={item.path}
                              to={item.path}
                              onClick={() => setAdminMenuOpen(false)}
                              className={`px-4 py-2.5 text-sm flex items-center gap-3 hover:bg-gray-100 dark:hover:bg-gray-700 transition ${
                                isActive(item.path)
                                  ? 'text-blue-600 dark:text-blue-400 font-medium bg-blue-50 dark:bg-gray-700/50'
                                  : 'text-gray-700 dark:text-gray-300'
                              }`}
                            >
                              <span className="text-base">{item.icon}</span>
                              <span>{item.label}</span>
                            </Link>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                </>
              )}
            </div>
          )}

          {/* Desktop Right Side — lg */}
          <div className="hidden lg:flex items-center space-x-1">
            {isAuthenticated && <NotificationDropdown />}
            
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg hover:bg-blue-500 dark:hover:bg-gray-700 transition"
              title={theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
            >
              {theme === 'dark' ? (
                <Sun className="w-5 h-5" />
              ) : (
                <Moon className="w-5 h-5" />
              )}
            </button>
            
            {isAuthenticated && (
              <a
                href="/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg hover:bg-blue-500 dark:hover:bg-gray-700 transition"
                title="📚 API"
              >
                📚
              </a>
            )}

            {isAuthenticated && user ? (
              <div className="flex items-center gap-1">
                <Link 
                  to="/profile" 
                  className="p-2 rounded-lg hover:bg-blue-500 dark:hover:bg-gray-700 transition"
                  title={user.username}
                >
                  <UserCog className="w-5 h-5" />
                </Link>
                <button
                  onClick={handleLogout}
                  className="p-2 rounded-lg hover:bg-red-600 transition"
                  title="Выйти"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            ) : (
              <>
                <Link to="/login" className="hover:bg-blue-500 dark:hover:bg-gray-700 px-3 py-2 rounded-lg transition text-sm">
                  Вход
                </Link>
                <Link to="/register" className="hover:bg-blue-500 dark:hover:bg-gray-700 px-3 py-2 rounded-lg transition text-sm">
                  Регистрация
                </Link>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex lg:hidden items-center gap-2">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg hover:bg-blue-500 dark:hover:bg-gray-700 transition"
              title={theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
            >
              {theme === 'dark' ? (
                <Sun className="w-5 h-5" />
              ) : (
                <Moon className="w-5 h-5" />
              )}
            </button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg hover:bg-blue-500 dark:hover:bg-gray-700 transition"
              aria-label="Menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

{/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-blue-500 dark:border-gray-700 pb-4">
            <div className="flex flex-col space-y-1 pt-3">
              {isAuthenticated && (
                <>
                  {navItems.map((item) => (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={closeMobileMenu}
                      className={`px-3 py-3 rounded-lg transition text-sm flex items-center gap-3 ${
                        isActive(item.path)
                          ? 'bg-blue-700 dark:bg-gray-700 text-white'
                          : 'hover:bg-blue-500 dark:hover:bg-gray-700'
                      }`}
                    >
                      <span className="text-lg">{item.icon}</span>
                      <span>{item.label}</span>
                    </Link>
                  ))}
                  
                  {isAdmin && (
                    <>
                      <div className="border-t border-blue-400 dark:border-gray-600 my-2" />
                      <div className="px-3 py-2 text-xs font-semibold text-blue-200 dark:text-gray-400 uppercase tracking-wider">
                        Управление
                      </div>
                      {adminItems.map((item) => (
                        <Link
                          key={item.path}
                          to={item.path}
                          onClick={closeMobileMenu}
                          className={`px-3 py-3 rounded-lg transition text-sm flex items-center gap-3 ${
                            isActive(item.path)
                              ? 'bg-blue-700 dark:bg-gray-700 text-white'
                              : 'hover:bg-blue-500 dark:hover:bg-gray-700'
                          }`}
                        >
                          <span className="text-lg">{item.icon}</span>
                          <span>{item.label}</span>
                        </Link>
                      ))}
                    </>
                  )}
                </>
              )}
              
              <div className="border-t border-blue-500 dark:border-gray-700 my-2 pt-2">
                {isAuthenticated && user ? (
                  <>
                    <div className="px-3 py-2 text-sm text-blue-200 dark:text-gray-400 flex items-center gap-2">
                      <UserCog className="w-4 h-4" />
                      {user.username}
                    </div>
                    <Link
                      to="/profile"
                      onClick={closeMobileMenu}
                      className="block px-3 py-3 rounded-lg hover:bg-blue-500 dark:hover:bg-gray-700 transition text-sm flex items-center gap-3"
                    >
                      <span>👤</span>
                      <span>Личный кабинет</span>
                    </Link>
                    <a
                      href="/docs"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block px-3 py-3 rounded-lg hover:bg-blue-500 dark:hover:bg-gray-700 transition text-sm flex items-center gap-3"
                    >
                      <span>📚</span>
                      <span>API документация</span>
                    </a>
                    <button
                      onClick={handleLogout}
                      className="w-full text-left px-3 py-3 rounded-lg hover:bg-red-600 transition text-sm flex items-center gap-3"
                    >
                      <span>🚪</span>
                      <span>Выйти</span>
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      to="/login"
                      onClick={closeMobileMenu}
                      className="block px-3 py-3 rounded-lg hover:bg-blue-500 dark:hover:bg-gray-700 transition text-sm flex items-center gap-3"
                    >
                      <span>🔑</span>
                      <span>Вход</span>
                    </Link>
                    <Link
                      to="/register"
                      onClick={closeMobileMenu}
                      className="block px-3 py-3 rounded-lg hover:bg-blue-500 dark:hover:bg-gray-700 transition text-sm flex items-center gap-3"
                    >
                      <span>📝</span>
                      <span>Регистрация</span>
                    </Link>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
