import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import RegisterForm from '../components/forms/RegisterForm';

const Register: React.FC = () => {
  const { register, loading, error, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  React.useEffect(() => {
    if (isAuthenticated) {
      navigate('/assets');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (data: any) => {
    try {
      await register(data);
      navigate('/assets');
    } catch (err) {
      console.error('Registration failed:', err);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-gray-100">
            Регистрация
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
            Создайте учетную запись
          </p>
        </div>
        <RegisterForm onSubmit={handleSubmit} loading={loading} />
        {error && (
          <div className="bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-600 text-red-700 dark:text-red-300 px-4 py-3 rounded relative">
            {error}
          </div>
        )}
        <div className="text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Уже есть учетная запись?{' '}
            <Link to="/login" className="font-medium text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 transition-colors">
              Войдите
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
