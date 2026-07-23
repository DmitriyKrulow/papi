import React from 'react';

interface ProfileFormProps {
  onSubmit: (data: ProfileFormData) => void;
  loading?: boolean;
  user: any;
}

interface ProfileFormData {
  username: string;
  email: string;
  full_name?: string;
  phone?: string;
}

const ProfileForm: React.FC<ProfileFormProps> = ({ onSubmit, loading = false, user }) => {
  const [formData, setFormData] = React.useState<ProfileFormData>({ username: '', email: '', full_name: '', phone: '' });
  const [errors, setErrors] = React.useState<Partial<ProfileFormData>>({});

  React.useEffect(() => {
    if (user) {
      setFormData({
        username: user.username || '',
        email: user.email || '',
        full_name: user.full_name || '',
        phone: user.phone || '',
      });
    }
  }, [user]);

  const validate = () => {
    const newErrors: Partial<ProfileFormData> = {};
    
    if (!formData.username.trim()) {
      newErrors.username = 'Обязательное поле';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Минимум 3 символа';
    } else if (formData.username.length > 50) {
      newErrors.username = 'Максимум 50 символов';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Обязательное поле';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Невалидный email';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name as keyof ProfileFormData]) {
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
        <label className="block text-sm font-medium mb-1">Имя пользователя</label>
        <input
          name="username"
          value={formData.username}
          onChange={handleChange}
          className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500"
          placeholder="Введите имя пользователя"
          type="text"
        />
        {errors.username && (
          <p className="text-red-500 text-xs mt-1">{errors.username}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Email</label>
        <input
          name="email"
          value={formData.email}
          onChange={handleChange}
          className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500"
          placeholder="Введите email"
          type="email"
        />
        {errors.email && (
          <p className="text-red-500 text-xs mt-1">{errors.email}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">ФИО</label>
        <input
          name="full_name"
          value={formData.full_name || ''}
          onChange={handleChange}
          className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500"
          placeholder="Иванов Иван Иванович"
          type="text"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Телефон</label>
        <input
          name="phone"
          value={formData.phone || ''}
          onChange={handleChange}
          className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500"
          placeholder="+7 (999) 123-45-67"
          type="tel"
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
      >
        {loading ? 'Сохранение...' : 'Сохранить'}
      </button>
    </form>
  );
};

export default ProfileForm;
