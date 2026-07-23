import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import RegisterForm from '../components/forms/RegisterForm';

const Register: React.FC = () => {
  const { register, loading, error } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (data: any) => {
    try {
      await register(data);
      navigate('/assets');
    } catch (err) {
      console.error('Registration failed:', err);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Регистрация
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Создайте учетную запись
          </p>
        </div>
        <RegisterForm onSubmit={handleSubmit} loading={loading} />
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
            {error}
          </div>
        )}
        <div className="text-center">
          <p className="text-sm text-gray-600">
            Уже есть учетная запись?{' '}
            <a href="/login" className="font-medium text-blue-600 hover:text-blue-500">
              Войдите
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
