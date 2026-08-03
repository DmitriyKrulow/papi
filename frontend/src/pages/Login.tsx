import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import LoginForm from '../components/forms/LoginForm';

const Login: React.FC = () => {
  const { login, loading, error, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  React.useEffect(() => {
    if (isAuthenticated) {
      navigate('/assets');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (data: any) => {
    try {
      await login(data);
      navigate('/assets');
    } catch (err) {
      console.error('Login failed:', err);
    }
  };

  return (
    <div className="flex flex-1 items-center justify-center relative overflow-hidden py-12">
      {/* No background */}
      <div className="absolute inset-0"></div>

      {/* Login card — прозрачная, через неё виден фон, отделена только тенью и границей */}
      <div className="relative z-10 w-full max-w-md mx-4">
        <div className="bg-transparent backdrop-blur-2xl rounded-3xl shadow-[0_20px_60px_rgba(0,0,0,0.12)] dark:shadow-[0_20px_60px_rgba(0,0,0,0.4)] p-8 md:p-10 animate-fade-in-up">
          {/* Logo/Icon */}
          <div className="flex justify-center mb-8">
            <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg transform hover:scale-105 transition-transform duration-300">
              <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
          </div>

          {/* Header */}
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Добро пожаловать</h2>
            <p className="text-gray-600 dark:text-gray-300 text-sm">Войдите в свою учетную запись</p>
          </div>

          {/* Form */}
          <LoginForm onSubmit={handleSubmit} loading={loading} />

          {/* Error message */}
          {error && (
            <div className="mt-4 bg-red-50 dark:bg-red-500/20 border border-red-200 dark:border-red-500/50 text-red-700 dark:text-red-200 px-4 py-3 rounded-xl text-sm">
              {error}
            </div>
          )}

          <div className="pt-4 border-t border-gray-200 dark:border-white/10">
            <p className="text-center text-sm text-gray-600 dark:text-gray-300">
              Забыли пароль?{' '}
              <a href="/password-reset" className="font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors duration-200">
                Написать заявку
              </a>
            </p>
            
            <p className="text-center text-sm text-gray-600 dark:text-gray-300 mt-3">
              Нет учетной записи?{' '}
              <a href="/register" className="font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors duration-200">
                Зарегистрируйтесь
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
