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
  } = useForm<DepartmentFormData>({
    resolver: zodResolver(departmentSchema),
    defaultValues: defaultValue || {
      is_active: true,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Название</label>
          <Controller
            name="name"
            control={control}
            render={({ field }) => (
              <input {...field} className="w-full px-3 py-2 border rounded-md" />
            )}
          />
          {errors.name && <p className="text-red-500 text-xs">{errors.name.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Код</label>
          <Controller
            name="code"
            control={control}
            render={({ field }) => (
              <input {...field} className="w-full px-3 py-2 border rounded-md" />
            )}
          />
          {errors.code && <p className="text-red-500 text-xs">{errors.code.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Руководитель</label>
          <Controller
            name="head"
            control={control}
            render={({ field }) => (
              <input {...field} className="w-full px-3 py-2 border rounded-md" />
            )}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Телефон</label>
          <Controller
            name="phone"
            control={control}
            render={({ field }) => (
              <input {...field} type="tel" className="w-full px-3 py-2 border rounded-md" />
            )}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Email</label>
          <Controller
            name="email"
            control={control}
            render={({ field }) => (
              <input {...field} type="email" className="w-full px-3 py-2 border rounded-md" />
            )}
          />
          {errors.email && <p className="text-red-500 text-xs">{errors.email.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Местоположение</label>
          <Controller
            name="location"
            control={control}
            render={({ field }) => (
              <input {...field} className="w-full px-3 py-2 border rounded-md" />
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
            <textarea {...field} className="w-full px-3 py-2 border rounded-md" rows={3} />
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
