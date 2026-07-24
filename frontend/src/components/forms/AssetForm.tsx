// frontend/src/components/forms/AssetForm.tsx
import React, { useState } from 'react';

interface AssetFormProps {
  onSubmit: (data: any) => void;
  defaultValue?: any;
  loading?: boolean;
}

const AssetForm: React.FC<AssetFormProps> = ({ onSubmit, defaultValue, loading }) => {
  const [formData, setFormData] = useState({
    inventory_number: defaultValue?.inventory_number || '',
    name: defaultValue?.name || '',
    description: defaultValue?.description || '',
    model: defaultValue?.model || '',
    asset_type: defaultValue?.asset_type || '',
    status: defaultValue?.status || 'active',
    purchase_price: defaultValue?.purchase_price || 0,
    current_value: defaultValue?.current_value || 0,
    department_code: defaultValue?.department_code || '',
    responsible_person: defaultValue?.responsible_person || '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'number' ? parseFloat(value) || 0 : value,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Инвентарный номер *</label>
          <input
            type="text"
            name="inventory_number"
            value={formData.inventory_number}
            onChange={handleChange}
            required
            disabled={loading}
            className="mt-1 w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Название *</label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            disabled={loading}
            className="mt-1 w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Описание</label>
        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          rows={3}
          disabled={loading}
          className="mt-1 w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Модель</label>
          <input
            type="text"
            name="model"
            value={formData.model}
            onChange={handleChange}
            disabled={loading}
            className="mt-1 w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Тип актива</label>
          <input
            type="text"
            name="asset_type"
            value={formData.asset_type}
            onChange={handleChange}
            disabled={loading}
            className="mt-1 w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Статус</label>
        <select
          name="status"
          value={formData.status}
          onChange={handleChange}
          disabled={loading}
          className="mt-1 w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
        >
          <option value="active">Активен</option>
          <option value="maintenance">На ремонте</option>
          <option value="reserved">В резерве</option>
          <option value="decommissioned">Выведен</option>
          <option value="written_off">Списан</option>
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Цена покупки (₽)</label>
          <input
            type="number"
            name="purchase_price"
            value={formData.purchase_price}
            onChange={handleChange}
            step="0.01"
            min="0"
            disabled={loading}
            className="mt-1 w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Текущая стоимость (₽)</label>
          <input
            type="number"
            name="current_value"
            value={formData.current_value}
            onChange={handleChange}
            step="0.01"
            min="0"
            disabled={loading}
            className="mt-1 w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Подразделение</label>
          <input
            type="text"
            name="department_code"
            value={formData.department_code}
            onChange={handleChange}
            disabled={loading}
            className="mt-1 w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Ответственное лицо</label>
          <input
            type="text"
            name="responsible_person"
            value={formData.responsible_person}
            onChange={handleChange}
            disabled={loading}
            className="mt-1 w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Сохранение...' : 'Сохранить'}
      </button>
    </form>
  );
};

export default AssetForm;