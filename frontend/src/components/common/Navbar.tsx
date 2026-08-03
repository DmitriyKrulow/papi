// frontend/src/components/common/Navbar.tsx
import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useTheme } from '../../hooks/useTheme';
import { Sun, Moon, Menu, X, ChevronDown } from 'lucide-react';

const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isAuthenticated, isAdmin } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  const navItems = [
    { path: '/', label: '🏠 Главная' },
    { path: '/dashboard', label: '📊 Дашборд' },
    { path: '/assets', label: '📦 Активы' },
    { path: '/repairs', label: '🔧 Ремонты' },
  ];

  const adminItems = [
    { path: '/admin', label: '⚙️ Админка' },
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
          <Link to="/" className="text-xl font-bold flex-shrink-0" onClick={closeMobileMenu}>
            🏗️ PAPI
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex items-center space-x-2">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-3 py-2 rounded-lg transition text-sm ${
                  isActive(item.path)
                    ? 'bg-blue-700 dark:bg-gray-700 text-white'
                    : 'hover:bg-blue-500 dark:hover:bg-gray-700'
                }`}
              >
                {item.label}
              </Link>
            ))}
            {isAdmin && adminItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-3 py-2 rounded-lg transition text-sm ${
                  isActive(item.path)
                    ? 'bg-blue-700 dark:bg-gray-700 text-white'
                    : 'hover:bg-blue-500 dark:hover:bg-gray-700'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </div>

          {/* Desktop Right Side */}
          <div className="hidden lg:flex items-center space-x-3">
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
            
            <a
              href="/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:bg-blue-500 dark:hover:bg-gray-700 px-2 py-2 rounded-lg transition"
              title="📚 API"
            >
              📚
            </a>

            {isAuthenticated && user ? (
              <>
                <Link to="/profile" className="hover:bg-blue-500 dark:hover:bg-gray-700 px-3 py-2 rounded-lg transition flex items-center gap-1">
                  <span className="text-sm">👤</span>
                  <span className="text-sm truncate max-w-[100px]">{user.username}</span>
                </Link>
                {isAdmin && (
                  <Link to="/admin" className="hover:bg-blue-500 dark:hover:bg-gray-700 px-3 py-2 rounded-lg transition text-sm">
                    ⚙️
                  </Link>
                )}
                <button
                  onClick={handleLogout}
                  className="hover:bg-blue-500 dark:hover:bg-gray-700 px-3 py-2 rounded-lg transition text-sm"
                >
                  Выйти
                </button>
              </>
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
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={closeMobileMenu}
                  className={`px-3 py-3 rounded-lg transition text-sm ${
                    isActive(item.path)
                      ? 'bg-blue-700 dark:bg-gray-700 text-white'
                      : 'hover:bg-blue-500 dark:hover:bg-gray-700'
                  }`}
                >
                  {item.label}
                </Link>
              ))}
              {isAdmin && adminItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={closeMobileMenu}
                  className={`px-3 py-3 rounded-lg transition text-sm ${
                    isActive(item.path)
                      ? 'bg-blue-700 dark:bg-gray-700 text-white'
                      : 'hover:bg-blue-500 dark:hover:bg-gray-700'
                  }`}
                >
                  {item.label}
                </Link>
              ))}
              
              <div className="border-t border-blue-500 dark:border-gray-700 my-2 pt-2">
                {isAuthenticated && user ? (
                  <>
                    <div className="px-3 py-2 text-sm text-blue-200 dark:text-gray-400">
                      👤 {user.username}
                    </div>
                    <Link
                      to="/profile"
                      onClick={closeMobileMenu}
                      className="block px-3 py-3 rounded-lg hover:bg-blue-500 dark:hover:bg-gray-700 transition text-sm"
                    >
                      👤 Личный кабинет
                    </Link>
                    {isAdmin && (
                      <Link
                        to="/admin"
                        onClick={closeMobileMenu}
                        className="block px-3 py-3 rounded-lg hover:bg-blue-500 dark:hover:bg-gray-700 transition text-sm"
                      >
                        ⚙️ Админ-панель
                      </Link>
                    )}
                    <a
                      href="/docs"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block px-3 py-3 rounded-lg hover:bg-blue-500 dark:hover:bg-gray-700 transition text-sm"
                    >
                      📚 API документация
                    </a>
                    <button
                      onClick={handleLogout}
                      className="w-full text-left px-3 py-3 rounded-lg hover:bg-blue-500 dark:hover:bg-gray-700 transition text-sm"
                    >
                      🚪 Выйти
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      to="/login"
                      onClick={closeMobileMenu}
                      className="block px-3 py-3 rounded-lg hover:bg-blue-500 dark:hover:bg-gray-700 transition text-sm"
                    >
                      🔑 Вход
                    </Link>
                    <Link
                      to="/register"
                      onClick={closeMobileMenu}
                      className="block px-3 py-3 rounded-lg hover:bg-blue-500 dark:hover:bg-gray-700 transition text-sm"
                    >
                      📝 Регистрация
                    </Link>
                    <a
                      href="/docs"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block px-3 py-3 rounded-lg hover:bg-blue-500 dark:hover:bg-gray-700 transition text-sm"
                    >
                      📚 API документация
                    </a>
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
