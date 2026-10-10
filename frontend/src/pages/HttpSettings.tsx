// frontend/src/pages/HttpSettings.tsx
import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';

interface HttpSettings {
  https_enabled: boolean;
  https_domain: string;
  https_email: string;
  https_port: number;
  http_warning_enabled: boolean;
  frontend_url: string;
  system_name: string;
}

interface HttpStatus {
  mode: string;
  enabled: boolean;
  domain: string;
  certificate_valid: boolean;
  days_remaining: number;
  error: string | null;
}

const HttpSettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<HttpSettings>({
    https_enabled: true,
    https_domain: '',
    https_email: '',
    https_port: 443,
    http_warning_enabled: true,
    frontend_url: '',
    system_name: 'PAPI Система',
  });
  const [httpStatus, setHttpStatus] = useState<HttpStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [restarting, setRestarting] = useState(false);
  const [urlError, setUrlError] = useState<string>('');
  const [urlChanged, setUrlChanged] = useState(false);

  const fetchSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/system-settings/config', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setSettings({
          https_enabled: data.https_enabled ?? true,
          https_domain: data.https_domain || '',
          https_email: data.https_email || '',
          https_port: data.https_port || 443,
          http_warning_enabled: data.http_warning_enabled ?? true,
          frontend_url: data.frontend_url || '',
          system_name: data.system_name || 'PAPI Система',
        });
      }
    } catch (err) {
      console.error('Failed to fetch settings:', err);
    }
  };

  const fetchHttpStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/system-settings/https-status', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setHttpStatus(data);
      }
    } catch (err) {
      console.error('Failed to fetch HTTPS status:', err);
    }
  };

  const validateFrontendUrl = (url: string): string => {
    if (!url.trim()) return '';
    
    try {
      const parsed = new URL(url);
      if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
        return 'URL должен использовать протокол http:// или https://';
      }
      
      const hostname = parsed.hostname.toLowerCase();
      if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.') || hostname.startsWith('10.')) {
        return 'URL не может быть внутренним (localhost/127.0.0.1/private IP). QR-код должен быть доступен извне.';
      }
      
      return '';
    } catch {
      return 'Введите корректный URL (напр. https://example.com)';
    }
  };

  const handleFrontendUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSettings({...settings, frontend_url: value});
    
    if (value.trim()) {
      const error = validateFrontendUrl(value);
      setUrlError(error);
      
      // Track if URL actually changed from saved value
      const oldSettings = { frontend_url: '' };
      // We'll compare on save instead
    } else {
      setUrlError('');
    }
  };

  useEffect(() => {
    fetchSettings();
    fetchHttpStatus();
    setLoading(false);
  }, []);

  const handleSave = async () => {
    try {
      setSaving(true);
      
      // Validate frontend URL before saving
      if (settings.frontend_url.trim()) {
        const error = validateFrontendUrl(settings.frontend_url);
        if (error) {
          setUrlError(error);
          toast.error(error);
          return;
        }
        setUrlError('');
      }
      
      const token = localStorage.getItem('token');
      
      // Check if frontend_url changed
      const oldSettingsResponse = await fetch('/api/system-settings/config', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      let urlWasChanged = false;
      if (oldSettingsResponse.ok) {
        const oldData = await oldSettingsResponse.json();
        if (oldData.frontend_url && oldData.frontend_url !== settings.frontend_url) {
          urlWasChanged = true;
          setUrlChanged(true);
        }
      }
      
      const response = await fetch('/api/system-settings/config', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });

      if (response.ok) {
        const msg = urlWasChanged 
          ? 'Настройки сохранены. Не забудьте перепечатать бирки с новыми QR-кодами!' 
          : 'Настройки сохранены. Перезапустите frontend для применения HTTPS.';
        toast.success(msg);
        fetchHttpStatus();
        
        if (urlWasChanged) {
          setTimeout(() => setUrlChanged(false), 10000);
        }
      } else {
        const err = await response.json();
        toast.error(err.detail || 'Ошибка сохранения');
      }
    } catch (err) {
      toast.error('Ошибка соединения');
    } finally {
      setSaving(false);
    }
  };

  const handleRestart = async () => {
    try {
      setRestarting(true);
      const token = localStorage.getItem('token');
      const response = await fetch('/api/system-settings/restart-https', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        toast.success('Frontend перезапускается...');
        setTimeout(() => {
          fetchHttpStatus();
          setLoading(false);
        }, 15000);
      } else {
        const err = await response.json();
        toast.error(err.detail || 'Ошибка перезапуска');
      }
    } catch (err) {
      toast.error('Ошибка соединения');
    } finally {
      setRestarting(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8 text-gray-500">Загрузка...</div>;
  }

  return (
    <div className="space-y-6">
      {/* HTTPS Status */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 border border-gray-100 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">
          🔒 Статус HTTPS
        </h2>
        
        {httpStatus?.enabled && httpStatus.domain ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              {httpStatus.mode === 'https' && httpStatus.certificate_valid ? (
                <span className="text-green-500 text-xl">✅</span>
              ) : httpStatus.mode === 'http' ? (
                <span className="text-yellow-500 text-xl">⚠️</span>
              ) : (
                <span className="text-red-500 text-xl">❌</span>
              )}
              <span className="font-medium text-gray-900 dark:text-gray-100">
                {httpStatus.mode === 'https' && httpStatus.certificate_valid
                  ? 'HTTPS активен'
                  : httpStatus.mode === 'http'
                  ? 'HTTP режим'
                  : 'HTTPS не настроен'}
              </span>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500 dark:text-gray-400">Домен:</span>
                <p className="font-medium text-gray-900 dark:text-gray-100">{httpStatus.domain}</p>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Срок действия:</span>
                {httpStatus.mode === 'http' ? (
                  <p className="font-medium text-yellow-600 dark:text-yellow-400">HTTP режим</p>
                ) : httpStatus.days_remaining > 30 ? (
                  <p className="font-medium text-green-600 dark:text-green-400">
                    {httpStatus.days_remaining} дней
                  </p>
                ) : httpStatus.days_remaining > 0 ? (
                  <p className="font-medium text-yellow-600 dark:text-yellow-400">
                    {httpStatus.days_remaining} дней
                  </p>
                ) : (
                  <p className="font-medium text-red-600 dark:text-red-400">Истёк</p>
                )}
              </div>
            </div>
            
            {httpStatus.error && (
              <div className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-300 px-4 py-2 rounded text-sm">
                ⚠️ {httpStatus.error}
              </div>
            )}
          </div>
        ) : (
          <div className="text-gray-500 dark:text-gray-400">
            HTTPS не настроен. Настройте домен и email ниже, затем перезапустите frontend.
          </div>
        )}
      </div>

      {/* General Settings */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 border border-gray-100 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">
          🌐 Основные настройки
        </h2>
        
        <div className="space-y-4">
          {/* System Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Название системы
            </label>
            <input
              type="text"
              placeholder="PAPI Система"
              value={settings.system_name}
              onChange={(e) => setSettings({...settings, system_name: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
          </div>

          {/* Frontend URL — используется в QR-кодах */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              URL фронтенда для QR-кодов
            </label>
            <input
              type="url"
              placeholder="https://example.com"
              value={settings.frontend_url}
              onChange={handleFrontendUrlChange}
              className={`w-full px-3 py-2 border rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 ${
                urlError ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
              }`}
            />
            {urlError ? (
              <p className="text-xs text-red-600 dark:text-red-400 mt-1">⚠️ {urlError}</p>
            ) : (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Базовый URL, который будет зашифрован в QR-кодах маркировки и инвентаризации. 
                Должен быть доступен извне (не localhost). Без trailing slash.
              </p>
            )}
          </div>
        </div>
      </div>

      {/* HTTPS Settings Form */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 border border-gray-100 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">
          ⚙️ Настройки HTTPS
        </h2>
        
        <div className="space-y-4">
          {/* HTTPS Enabled */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Включить HTTPS
            </label>
            <select
              value={settings.https_enabled ? 'true' : 'false'}
              onChange={(e) => setSettings({...settings, https_enabled: e.target.value === 'true'})}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            >
              <option value="true">✅ Включён (по умолчанию)</option>
              <option value="false">❌ Выключен (только HTTP)</option>
            </select>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              При включении система автоматически получит SSL-сертификат от Let's Encrypt
            </p>
          </div>

          {/* Domain */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Доменное имя
            </label>
            <input
              type="text"
              placeholder="например: мастербайт.рф"
              value={settings.https_domain}
              onChange={(e) => setSettings({...settings, https_domain: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Домен должен указывать на IP вашего сервера (DNS A-запись). Система автоматически конвертирует в punycode.
            </p>
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Email для уведомлений Let's Encrypt
            </label>
            <input
              type="email"
              placeholder="admin@example.com"
              value={settings.https_email}
              onChange={(e) => setSettings({...settings, https_email: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Let's Encrypt будет отправлять уведомления об истечении сертификатов
            </p>
          </div>

          {/* Port */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              HTTPS порт
            </label>
            <input
              type="number"
              value={settings.https_port}
              onChange={(e) => setSettings({...settings, https_port: parseInt(e.target.value) || 443})}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Для продакшена используйте 443
            </p>
          </div>

          {/* HTTP Warning */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="http_warning"
              checked={settings.http_warning_enabled}
              onChange={(e) => setSettings({...settings, http_warning_enabled: e.target.checked})}
              className="rounded"
            />
            <label htmlFor="http_warning" className="text-sm text-gray-700 dark:text-gray-300">
              Показывать предупреждение при подключении по HTTP
            </label>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3 mt-6">
          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm disabled:opacity-50"
          >
            {saving ? 'Сохранение...' : '💾 Сохранить настройки'}
          </button>
          
          <button
            onClick={handleRestart}
            disabled={restarting}
            className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition text-sm disabled:opacity-50"
          >
            {restarting ? 'Перезапуск...' : '🔄 Перезапустить frontend'}
          </button>
        </div>
      </div>

      {/* QR Regeneration Notice */}
      {urlChanged && (
        <div className="bg-orange-50 dark:bg-orange-900/30 border border-orange-200 dark:border-orange-800 rounded-lg p-4">
          <h3 className="font-medium text-orange-900 dark:text-orange-300 mb-2">
            ⚠️ URL QR-кодов изменён
          </h3>
          <p className="text-sm text-orange-800 dark:text-orange-400 mb-3">
            Вы обновили URL фронтенда. Все <strong>новые</strong> QR-коды будут использовать новый адрес.
            <br/>
            Для обновления <strong>уже напечатанных</strong> бирок:
          </p>
          <div className="flex gap-3">
            <button
              onClick={() => window.location.href = '/#/marking'}
              className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition text-sm"
            >
              🖨️ Перепечатать бирки
            </button>
            <button
              onClick={() => setUrlChanged(false)}
              className="bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition text-sm"
            >
              Понятно
            </button>
          </div>
        </div>
      )}

      {/* Info */}
      <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 dark:text-blue-300 mb-2">ℹ️ Как это работает</h3>
        <ul className="text-sm text-blue-800 dark:text-blue-400 space-y-1 list-disc list-inside">
          <li>При первом запуске система автоматически получит SSL-сертификат от Let's Encrypt</li>
          <li>Сертификат действителен 90 дней с автоматическим обновлением</li>
          <li>Доменное имя автоматически конвертируется в punycode (например: мастербайт.рф → xn--80aacpwn4agjf.xn--p1ai)</li>
          <li>Все HTTP-запросы перенаправляются на HTTPS</li>
          <li>Для активации изменений перезапустите frontend кнопкой выше</li>
        </ul>
      </div>
    </div>
  );
};

export default HttpSettingsPage;
