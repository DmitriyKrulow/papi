// frontend/src/components/assets/EditAssetForm.tsx
import React from 'react';
import { useForm } from 'react-hook-form';
import type { Asset } from '../../types';

interface EditAssetFormProps {
  existingAsset: Asset;
  onSubmit: (data: Asset) => Promise<void>;
  onClose: () => void;
}

interface FormData {
  inventory_number: string;
  name: string;
  description?: string;
  model?: string;
  manufacturer_code?: string;
  manufacturer_name?: string;
  purchase_price?: number;
  current_value?: number;
  status: string;
  location_address?: string;
  responsible_person?: string;
  department_code?: string;
}

const EditAssetForm: React.FC<EditAssetFormProps> = ({ existingAsset, onSubmit, onClose }) => {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<FormData>({
    defaultValues: {
      inventory_number: existingAsset.inventory_number,
      name: existingAsset.name,
      description: existingAsset.description || '',
      model: existingAsset.model || '',
      manufacturer_code: existingAsset.manufacturer_code || '',
      manufacturer_name: existingAsset.manufacturer_name || '',
      purchase_price: existingAsset.purchase_price || 0,
      current_value: existingAsset.current_value || 0,
      status: existingAsset.status,
      location_address: existingAsset.location_address || '',
      responsible_person: existingAsset.responsible_person || '',
      department_code: existingAsset.department_code || '',
    },
  });

  const handleSubmitForm = async (data: FormData) => {
    try {
      await onSubmit({
        ...existingAsset,
        inventory_number: data.inventory_number,
        name: data.name,
        description: data.description,
        model: data.model,
        manufacturer_code: data.manufacturer_code,
        manufacturer_name: data.manufacturer_name,
        purchase_price: data.purchase_price ? Number(data.purchase_price) : undefined,
        current_value: data.current_value ? Number(data.current_value) : undefined,
        status: data.status as Asset['status'],
        location_address: data.location_address,
        responsible_person: data.responsible_person,
        department_code: data.department_code,
      });
    } catch (error) {
      console.error('Ошибка отправки формы:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit(handleSubmitForm)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Инвентарный номер *
          </label>
          <input
            type="text"
            {...register('inventory_number', {
              required: 'Обязательное поле',
              minLength: {
                value: 3,
                message: 'Минимум 3 символа',
              },
            })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="INV-001"
          />
          {errors.inventory_number && (
            <p className="mt-1 text-sm text-red-600">{errors.inventory_number.message}</p>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Название *
          </label>
          <input
            type="text"
            {...register('name', {
              required: 'Обязательное поле',
              minLength: {
                value: 2,
                message: 'Минимум 2 символа',
              },
            })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Название актива"
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Модель
          </label>
          <input
            type="text"
            {...register('model')}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Модель"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Код производителя
          </label>
          <input
            type="text"
            {...register('manufacturer_code')}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Код производителя"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Производитель
        </label>
        <input
          type="text"
          {...register('manufacturer_name')}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Производитель"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Стоимость покупки (₽)
          </label>
          <input
            type="number"
            step="0.01"
            min="0"
            {...register('purchase_price', {
              valueAsNumber: true,
            })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="0.00"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Текущая стоимость (₽)
          </label>
          <input
            type="number"
            step="0.01"
            min="0"
            {...register('current_value', {
              valueAsNumber: true,
            })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="0.00"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Статус *
        </label>
        <select
          {...register('status', {
            required: 'Обязательное поле',
          })}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="active">Активен</option>
          <option value="maintenance">На ремонте</option>
          <option value="reserved">В резерве</option>
          <option value="decommissioned">Выведен</option>
          <option value="lost">Утерян</option>
          <option value="written_off">Списан</option>
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Адрес расположения
          </label>
          <input
            type="text"
            {...register('location_address')}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Адрес"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Ответственное лицо
          </label>
          <input
            type="text"
            {...register('responsible_person')}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="ФИО"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Код подразделения
        </label>
        <input
          type="text"
          {...register('department_code')}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Деп-001"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Описание
        </label>
        <textarea
          {...register('description')}
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Описание актива..."
        />
      </div>

      <div className="flex gap-3 pt-4">
        <button
          type="button"
          onClick={onClose}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition text-gray-700"
        >
          Отмена
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              Сохранение...
            </>
          ) : (
            'Сохранить'
          )}
        </button>
      </div>
    </form>
  );
};

export default EditAssetForm;
