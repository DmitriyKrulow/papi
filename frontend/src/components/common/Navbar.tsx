// frontend/src/components/common/Navbar.tsx
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isAuthenticated, isAdmin } = useAuth();

  const isActive = (path: string) => location.pathname === path;

  const navItems = [
    { path: '/', label: '🏠 Главная' },
    { path: '/dashboard', label: '📊 Дашборд' },
    { path: '/assets', label: '📦 Активы' },
  ];

  const adminItems = [
    { path: '/admin', label: '⚙️ Админка' },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-blue-600 text-white shadow-lg sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <Link to="/" className="text-xl font-bold">
              🏗️ PAPI
            </Link>
            <div className="flex space-x-4">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-3 py-2 rounded-lg transition ${
                    isActive(item.path)
                      ? 'bg-blue-700 text-white'
                      : 'hover:bg-blue-500'
                  }`}
                >
                  {item.label}
                </Link>
              ))}
              {isAdmin && adminItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-3 py-2 rounded-lg transition ${
                    isActive(item.path)
                      ? 'bg-blue-700 text-white'
                      : 'hover:bg-blue-500'
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
          <div className="flex items-center space-x-4">
            {isAuthenticated && user ? (
              <div className="flex items-center space-x-4">
                <Link to="/profile" className="hover:text-blue-200 transition">
                  👤 {user.username}
                </Link>
                {isAdmin && (
                  <Link to="/admin" className="hover:text-blue-200 transition">
                    ⚙️ Админка
                  </Link>
                )}
                <button
                  onClick={handleLogout}
                  className="px-3 py-2 rounded-lg hover:bg-blue-500 transition"
                >
                  Выйти
                </button>
              </div>
            ) : (
              <>
                <Link to="/login" className="hover:text-blue-200 transition">
                  Вход
                </Link>
                <Link to="/register" className="hover:text-blue-200 transition">
                  Регистрация
                </Link>
              </>
            )}
            <a
              href="/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-blue-200 transition"
            >
              📚 API
            </a>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;