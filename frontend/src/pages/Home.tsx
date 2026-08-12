// frontend/src/pages/Home.tsx
import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const Home: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  // Редирект авторизованных пользователей на дашборд
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Неавторизованный пользователь видит только общее описание
  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] text-center py-16 max-w-2xl mx-auto">
      <div className="mb-8">
        <div className="text-6xl mb-4">🏗️</div>
        <h1 className="text-4xl font-bold text-gray-800 dark:text-gray-100 mb-4">
          PAPI — Управление активами
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-400 mb-3">
          Система для управления основными средствами и активами предприятия
        </p>
        <p className="text-base text-gray-500 dark:text-gray-500">
          Для доступа к функционалу системы, пожалуйста, авторизуйтесь или зарегистрируйтесь.
        </p>
      </div>
      
      <div className="flex flex-col sm:flex-row gap-4">
        <Link
          to="/login"
          className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition inline-block font-medium"
        >
          🔑 Войти
        </Link>
        <Link
          to="/register"
          className="bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-100 px-8 py-3 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition inline-block font-medium"
        >
          📝 Зарегистрироваться
        </Link>
      </div>
    </div>
  );
};

export default Home;
