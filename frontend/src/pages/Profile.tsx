import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import ProfileForm from '../components/forms/ProfileForm';
import ChangePasswordForm from '../components/forms/ChangePasswordForm';

const Profile: React.FC = () => {
  const { user, updateProfile, changePassword, loading, error } = useAuth();
  const navigate = useNavigate();

  const handleProfileSubmit = async (data: any) => {
    try {
      await updateProfile(data);
      alert('Профиль успешно обновлен');
    } catch (err) {
      console.error('Profile update failed:', err);
    }
  };

  const handleChangePassword = async (data: any) => {
    try {
      await changePassword(data.oldPassword, data.newPassword);
      alert('Пароль успешно изменен');
    } catch (err) {
      console.error('Password change failed:', err);
    }
  };

  const handleLogout = () => {
    navigate('/login');
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900">Загрузка профиля...</h2>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">Личный кабинет</h2>
            <p className="mt-1 text-sm text-gray-500">
              Пользователь: <span className="font-medium">{user.username}</span>
            </p>
            <p className="text-sm text-gray-500">
              Email: <span className="font-medium">{user.email}</span>
            </p>
            <p className="text-sm text-gray-500">
              Роль: <span className="font-medium">{user.role}</span>
            </p>
          </div>
          
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mx-4 mb-4">
              {error}
            </div>
          )}

          <div className="px-4 py-5 sm:p-6 space-y-8">
            {/* Профиль */}
            <div>
              <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">Личные данные</h3>
              <ProfileForm onSubmit={handleProfileSubmit} loading={loading} user={user} />
            </div>

            {/* Смена пароля */}
            <div className="border-t border-gray-200 pt-6">
              <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">Безопасность</h3>
              <ChangePasswordForm onSubmit={handleChangePassword} loading={loading} />
            </div>
          </div>

          <div className="px-4 py-4 bg-gray-50 border-t border-gray-200 sm:px-6">
            <button
              onClick={handleLogout}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              Выйти
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
