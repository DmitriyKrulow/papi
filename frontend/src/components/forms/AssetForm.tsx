import React from 'react';
import { useForm, SubmitHandler, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

interface AssetFormProps {
  onSubmit: (data: AssetFormData) => void;
  defaultValue?: AssetFormData;
  loading?: boolean;
}

const assetSchema = z.object({
  inventory_number: z.string().min(1, 'Обязательное поле').max(50, 'Максимум 50 символов'),
  name: z.string().min(1, 'Обязательное поле').max(255, 'Максимум 255 символов'),
  description: z.string().max(65535, 'Максимум 65535 символов').optional(),
  model: z.string().max(255, 'Максимум 255 символов').optional(),
  manufacturer_code: z.string().max(100, 'Максимум 100 символов').optional(),
  manufacturer_name: z.string().max(255, 'Максимум 255 символов').optional(),
  country_of_origin: z.string().max(100, 'Максимум 100 символов').optional(),
  accounting_code: z.string().max(100, 'Максимум 100 символов').optional(),
  department_code: z.string().max(100, 'Максимум 100 символов').optional(),
  responsible_person: z.string().max(255, 'Максимум 255 символов').optional(),
  purchase_price: z.coerce.number().min(0, 'Не может быть отрицательным').optional(),
  current_value: z.coerce.number().min(0, 'Не может быть отрицательным').optional(),
  residual_value: z.coerce.number().min(0, 'Не может быть отрицательным').optional(),
  depreciation_rate: z.coerce.number().min(0).max(100, 'Максимум 100%').optional(),
  location: z.string().max(255, 'Максимум 255 символов').optional(),
  location_address: z.string().max(500, 'Максимум 500 символов').optional(),
  responsible_phone: z.string().max(50, 'Максимум 50 символов').optional(),
  purchase_date: z.coerce.date().optional(),
  commissioning_date: z.coerce.date().optional(),
  warranty_expiry: z.coerce.date().optional(),
  last_maintenance_date: z.coerce.date().optional(),
  next_maintenance_date: z.coerce.date().optional(),
  decommissioning_date: z.coerce.date().optional(),
  tags: z.array(z.string()).optional(),
  notes: z.string().max(65535, 'Максимум 65535 символов').optional(),
  is_active: z.boolean().optional(),
});

type AssetFormData = z.infer<typeof assetSchema>;

const AssetForm: React.FC<AssetFormProps> = ({ onSubmit, defaultValue, loading = false }) => {
  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AssetFormData>({
    resolver: zodResolver(assetSchema),
    defaultValues: defaultValue || {
      is_active: true,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Инвентарный номер</label>
          <Controller
            name="inventory_number"
            control={control}
            render={({ field }) => (
              <input
                {...field}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="Введите инвентарный номер"
              />
            )}
          />
          {errors.inventory_number && (
            <p className="text-red-500 text-xs">{errors.inventory_number.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Название</label>
          <Controller
            name="name"
            control={control}
            render={({ field }) => (
              <input
                {...field}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="Введите название"
              />
            )}
          />
          {errors.name && <p className="text-red-500 text-xs">{errors.name.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Модель</label>
          <Controller
            name="model"
            control={control}
            render={({ field }) => (
              <input
                {...field}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="Введите модель"
              />
            )}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Страна производства</label>
          <Controller
            name="country_of_origin"
            control={control}
            render={({ field }) => (
              <input
                {...field}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="Введите страну"
              />
            )}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Цена покупки</label>
          <Controller
            name="purchase_price"
            control={control}
            render={({ field }) => (
              <input
                {...field}
                type="number"
                className="w-full px-3 py-2 border rounded-md"
                placeholder="0.00"
              />
            )}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Текущая стоимость</label>
          <Controller
            name="current_value"
            control={control}
            render={({ field }) => (
              <input
                {...field}
                type="number"
                className="w-full px-3 py-2 border rounded-md"
                placeholder="0.00"
              />
            )}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Ставка амортизации (%)</label>
          <Controller
            name="depreciation_rate"
            control={control}
            render={({ field }) => (
              <input
                {...field}
                type="number"
                className="w-full px-3 py-2 border rounded-md"
                placeholder="0-100"
              />
            )}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Код подразделения</label>
          <Controller
            name="department_code"
            control={control}
            render={({ field }) => (
              <input
                {...field}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="DEPT-001"
              />
            )}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Ответственное лицо</label>
          <Controller
            name="responsible_person"
            control={control}
            render={({ field }) => (
              <input
                {...field}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="ФИО ответственного"
              />
            )}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Телефон ответственного</label>
          <Controller
            name="responsible_phone"
            control={control}
            render={({ field }) => (
              <input
                {...field}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="+7 (999) 000-00-00"
              />
            )}
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Описание</label>
        <Controller
          name="description"
          control={control}
          render={({ field }) => (
            <textarea
              {...field}
              className="w-full px-3 py-2 border rounded-md"
              rows={3}
              placeholder="Описание актива"
            />
          )}
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Адрес местоположения</label>
        <Controller
          name="location_address"
          control={control}
          render={({ field }) => (
            <input
              {...field}
              className="w-full px-3 py-2 border rounded-md"
              placeholder="Адрес"
            />
          )}
        />
      </div>

      <div className="flex items-center space-x-4">
        <label className="flex items-center">
          <Controller
            name="is_active"
            control={control}
            render={({ field }) => (
              <input
                type="checkbox"
                {...field}
                checked={field.value}
                onChange={field.onChange}
                className="mr-2"
              />
            )}
          />
          Активен
        </label>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Сохранение...' : 'Сохранить'}
      </button>
    </form>
  );
};

export default AssetForm;
