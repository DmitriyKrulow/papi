import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import toast from 'react-hot-toast';

const PasswordResetPage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [request, setRequest] = useState({
    username: '',
    email: '',
    full_name: '',
    reason: '',
  });
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  React.useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!request.username || !request.reason) {
      toast.error('Заполните обязательные поля');
      return;
    }
    setSubmitting(true);
    try {
      const response = await fetch('/api/password-reset/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });
      if (response.ok) {
        setSubmitted(true);
        setRequest({ username: '', email: '', full_name: '', reason: '' });
      } else {
        const errorData = await response.json().catch(() => ({}));
        toast.error(errorData.detail || 'Ошибка отправки заявки');
      }
    } catch {
      toast.error('Ошибка соединения с сервером');
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="flex flex-1 items-center justify-center py-12">
        <div className="bg-transparent rounded-3xl shadow-[0_20px_60px_rgba(0,0,0,0.12)] dark:shadow-[0_20px_60px_rgba(0,0,0,0.4)] p-8 md:p-10 animate-fade-in-up max-w-md w-full mx-4">
          <div className="text-center">
            <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Заявка отправлена</h2>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              Администратор рассмотрит вашу заявку и свяжется с вами для предоставления нового пароля.
            </p>
            <Link
              to="/login"
              className="inline-block px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-semibold hover:from-blue-600 hover:to-purple-700 transition"
            >
              Вернуться на вход
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 items-center justify-center relative overflow-hidden py-12">
      <div className="relative z-10 w-full max-w-lg mx-4">
        <div className="rounded-3xl shadow-[0_20px_60px_rgba(0,0,0,0.12)] dark:shadow-[0_20px_60px_rgba(0,0,0,0.4)] p-8 md:p-10 animate-fade-in-up">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-2xl flex items-center justify-center shadow-lg">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
              </svg>
            </div>
          </div>

          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">Запрос сброса пароля</h2>
            <p className="text-gray-600 dark:text-gray-300 text-sm">
              Забыли пароль? Отправьте заявку администратору
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Имя пользователя *</label>
              <input
                type="text"
                value={request.username}
                onChange={(e) => setRequest({ ...request, username: e.target.value })}
                className="w-full px-3 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-gray-900 border border-gray-300 placeholder-gray-500 dark:bg-gray-700 dark:text-white dark:border-gray-600"
                placeholder="Ваш логин"
                required
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Email (если известен)</label>
              <input
                type="email"
                value={request.email}
                onChange={(e) => setRequest({ ...request, email: e.target.value })}
                className="w-full px-3 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-gray-900 border border-gray-300 placeholder-gray-500 dark:bg-gray-700 dark:text-white dark:border-gray-600"
                placeholder="your@email.com"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">ФИО (если известно)</label>
              <input
                type="text"
                value={request.full_name}
                onChange={(e) => setRequest({ ...request, full_name: e.target.value })}
                className="w-full px-3 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-gray-900 border border-gray-300 placeholder-gray-500 dark:bg-gray-700 dark:text-white dark:border-gray-600"
                placeholder="Иванов Иван Иванович"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Причина запроса *</label>
              <textarea
                value={request.reason}
                onChange={(e) => setRequest({ ...request, reason: e.target.value })}
                className="w-full px-3 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-gray-900 border border-gray-300 placeholder-gray-500 dark:bg-gray-700 dark:text-white dark:border-gray-600"
                placeholder="Опишите, почему вам нужен сброс пароля"
                rows={3}
                required
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 px-4 bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-white font-semibold rounded-xl shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Отправка...' : 'Отправить заявку'}
            </button>
          </form>

          <div className="mt-6 pt-4 border-t border-gray-200 dark:border-white/10 text-center">
            <Link to="/login" className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300">
              Вспомнили пароль? Войти
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PasswordResetPage;
