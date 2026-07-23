import React from 'react';
import { useForm, SubmitHandler, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

interface EmployeeFormProps {
  onSubmit: (data: EmployeeFormData) => void;
  defaultValue?: EmployeeFormData;
  loading?: boolean;
}

const employeeSchema = z.object({
  department_id: z.number().int().positive({ message: 'Выберите подразделение' }),
  user_id: z.number().int().positive({ message: 'Выберите пользователя' }),
  first_name: z.string().min(1, 'Обязательное поле').max(100, 'Максимум 100 символов'),
  last_name: z.string().min(1, 'Обязательное поле').max(100, 'Максимум 100 символов'),
  middle_name: z.string().max(100, 'Максимум 100 символов').optional(),
  phone: z.string().max(50, 'Максимум 50 символов').optional(),
  email: z.string().email('Некорректный email').optional(),
  position: z.string().max(255, 'Максимум 255 символов').optional(),
  position_code: z.string().max(50, 'Максимум 50 символов').optional(),
  employee_number: z.string().max(50, 'Максимум 50 символов').optional(),
  hire_date: z.coerce.date().optional(),
  termination_date: z.coerce.date().optional(),
  is_active: z.boolean().optional(),
});

type EmployeeFormData = z.infer<typeof employeeSchema>;

const EmployeeForm: React.FC<EmployeeFormProps> = ({ onSubmit, defaultValue, loading = false }) => {
  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<EmployeeFormData>({
    resolver: zodResolver(employeeSchema),
    defaultValues: defaultValue || {
      is_active: true,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Имя</label>
          <Controller
            name="first_name"
            control={control}
            render={({ field }) => (
              <input {...field} className="w-full px-3 py-2 border rounded-md" />
            )}
          />
          {errors.first_name && (
            <p className="text-red-500 text-xs">{errors.first_name.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Фамилия</label>
          <Controller
            name="last_name"
            control={control}
            render={({ field }) => (
              <input {...field} className="w-full px-3 py-2 border rounded-md" />
            )}
          />
          {errors.last_name && (
            <p className="text-red-500 text-xs">{errors.last_name.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Отчество</label>
          <Controller
            name="middle_name"
            control={control}
            render={({ field }) => (
              <input {...field} className="w-full px-3 py-2 border rounded-md" />
            )}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Должность</label>
          <Controller
            name="position"
            control={control}
            render={({ field }) => (
              <input {...field} className="w-full px-3 py-2 border rounded-md" />
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
          <label className="block text-sm font-medium mb-1">Табельный номер</label>
          <Controller
            name="employee_number"
            control={control}
            render={({ field }) => (
              <input {...field} className="w-full px-3 py-2 border rounded-md" />
            )}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Дата приема</label>
          <Controller
            name="hire_date"
            control={control}
            render={({ field }) => (
              <input {...field} type="date" className="w-full px-3 py-2 border rounded-md" />
            )}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Дата увольнения</label>
          <Controller
            name="termination_date"
            control={control}
            render={({ field }) => (
              <input {...field} type="date" className="w-full px-3 py-2 border rounded-md" />
            )}
          />
        </div>
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

export default EmployeeForm;
