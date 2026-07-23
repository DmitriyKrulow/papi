import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import LoginForm from '../components/forms/LoginForm';

const Login: React.FC = () => {
  const { login, loading, error } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (data: any) => {
    try {
      await login(data);
      navigate('/assets');
    } catch (err) {
      console.error('Login failed:', err);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Вход в систему
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Войдите в свою учетную запись
          </p>
        </div>
        <LoginForm onSubmit={handleSubmit} loading={loading} />
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
            {error}
          </div>
        )}
        <div className="text-center">
          <p className="text-sm text-gray-600">
            Нет учетной записи?{' '}
            <a href="/register" className="font-medium text-blue-600 hover:text-blue-500">
              Зарегистрируйтесь
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
