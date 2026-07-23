import React from 'react';

interface ChangePasswordFormProps {
  onSubmit: (data: ChangePasswordFormData) => void;
  loading?: boolean;
}

interface ChangePasswordFormData {
  oldPassword: string;
  newPassword: string;
  confirmPassword: string;
}

const ChangePasswordForm: React.FC<ChangePasswordFormProps> = ({ onSubmit, loading = false }) => {
  const [formData, setFormData] = React.useState<ChangePasswordFormData>({ oldPassword: '', newPassword: '', confirmPassword: '' });
  const [errors, setErrors] = React.useState<Partial<ChangePasswordFormData>>({});

  const validate = () => {
    const newErrors: Partial<ChangePasswordFormData> = {};
    
    if (!formData.oldPassword) {
      newErrors.oldPassword = 'Обязательное поле';
    }
    
    if (!formData.newPassword) {
      newErrors.newPassword = 'Обязательное поле';
    } else if (formData.newPassword.length < 6) {
      newErrors.newPassword = 'Минимум 6 символов';
    }
    
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Подтвердите пароль';
    } else if (formData.newPassword !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Пароли не совпадают';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name as keyof ChangePasswordFormData]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      onSubmit(formData);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-1">Старый пароль</label>
        <input
          name="oldPassword"
          value={formData.oldPassword}
          onChange={handleChange}
          className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500"
          placeholder="Введите старый пароль"
          type="password"
        />
        {errors.oldPassword && (
          <p className="text-red-500 text-xs mt-1">{errors.oldPassword}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Новый пароль</label>
        <input
          name="newPassword"
          value={formData.newPassword}
          onChange={handleChange}
          className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500"
          placeholder="Введите новый пароль"
          type="password"
        />
        {errors.newPassword && (
          <p className="text-red-500 text-xs mt-1">{errors.newPassword}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Подтвердите новый пароль</label>
        <input
          name="confirmPassword"
          value={formData.confirmPassword}
          onChange={handleChange}
          className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500"
          placeholder="Повторите новый пароль"
          type="password"
        />
        {errors.confirmPassword && (
          <p className="text-red-500 text-xs mt-1">{errors.confirmPassword}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 transition-colors"
      >
        {loading ? 'Изменение...' : 'Изменить пароль'}
      </button>
    </form>
  );
};

export default ChangePasswordForm;
