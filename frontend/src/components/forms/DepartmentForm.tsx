import React from 'react';
import { useForm, SubmitHandler, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

interface DepartmentFormProps {
  onSubmit: (data: DepartmentFormData) => void;
  defaultValue?: DepartmentFormData;
  loading?: boolean;
}

const departmentSchema = z.object({
  organization_id: z.number().int().positive({ message: 'Обязательное поле' }),
  name: z.string().min(1, 'Обязательное поле').max(255, 'Максимум 255 символов'),
  code: z.string().min(1, 'Обязательное поле').max(50, 'Максимум 50 символов'),
  parent_id: z.number().int().positive().optional(),
  head: z.string().max(255, 'Максимум 255 символов').optional(),
  phone: z.string().max(50, 'Максимум 50 символов').optional(),
  email: z.string().email('Некорректный email').optional(),
  location: z.string().max(255, 'Максимум 255 символов').optional(),
  description: z.string().optional(),
  is_active: z.boolean().optional(),
});

type DepartmentFormData = z.infer<typeof departmentSchema>;

const DepartmentForm: React.FC<DepartmentFormProps> = ({
  onSubmit,
  defaultValue,
  loading = false,
}) => {
  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue,
  } = useForm<DepartmentFormData>({
    resolver: zodResolver(departmentSchema),
    defaultValues: {
      ...defaultValue,
      is_active: defaultValue?.is_active ?? true,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Название</label>
          <Controller
            name="name"
            control={control}
            render={({ field }) => (
              <input {...field} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" />
            )}
          />
          {errors.name && <p className="text-red-500 text-xs">{errors.name.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Код</label>
          <Controller
            name="code"
            control={control}
            render={({ field }) => (
              <input {...field} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" />
            )}
          />
          {errors.code && <p className="text-red-500 text-xs">{errors.code.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Руководитель</label>
          <Controller
            name="head"
            control={control}
            render={({ field }) => (
              <input {...field} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" />
            )}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Телефон</label>
          <Controller
            name="phone"
            control={control}
            render={({ field }) => (
              <input {...field} type="tel" className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" />
            )}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Email</label>
          <Controller
            name="email"
            control={control}
            render={({ field }) => (
              <input {...field} type="email" className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" />
            )}
          />
          {errors.email && <p className="text-red-500 text-xs">{errors.email.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Местоположение</label>
          <Controller
            name="location"
            control={control}
            render={({ field }) => (
              <input {...field} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" />
            )}
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Описание</label>
        <Controller
          name="description"
          control={control}
          render={({ field }) => (
            <textarea {...field} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" rows={3} />
          )}
        />
      </div>

        <div className="flex items-center space-x-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={!!watch('is_active')}
              onChange={(e) => setValue('is_active', e.target.checked)}
              className="mr-2"
            />
            Активно
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

export default DepartmentForm;
