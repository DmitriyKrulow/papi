import React from 'react';
import { useForm, SubmitHandler, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

interface RepairFormProps {
  onSubmit: (data: RepairFormData) => void;
  defaultValue?: RepairFormData;
  loading?: boolean;
  assetId?: number;
}

const repairSchema = z.object({
  title: z.string().min(1, 'Обязательное поле').max(255, 'Максимум 255 символов'),
  description: z.string().min(1, 'Обязательное поле'),
  asset_id: z.number().int().positive(),
  priority: z.enum(['low', 'medium', 'high', 'urgent']).default('medium'),
  created_by: z.number().int().positive(),
  desired_completion_date: z.coerce.date().optional(),
  deadline: z.coerce.date().optional(),
  estimated_cost: z.coerce.number().min(0, 'Не может быть отрицательным').optional(),
});

type RepairFormData = z.infer<typeof repairSchema>;

const RepairForm: React.FC<RepairFormProps> = ({
  onSubmit,
  defaultValue,
  loading = false,
  assetId,
}) => {
  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RepairFormData>({
    resolver: zodResolver(repairSchema),
    defaultValues: defaultValue || {
      priority: 'medium',
      asset_id: assetId || 0,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-1">Название</label>
        <Controller
          name="title"
          control={control}
          render={({ field }) => (
            <input
              {...field}
              className="w-full px-3 py-2 border rounded-md"
              placeholder="Краткое описание проблемы"
            />
          )}
        />
        {errors.title && <p className="text-red-500 text-xs">{errors.title.message}</p>}
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
              rows={4}
              placeholder="Подробное описание неисправности"
            />
          )}
        />
        {errors.description && (
          <p className="text-red-500 text-xs">{errors.description.message}</p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Приоритет</label>
          <Controller
            name="priority"
            control={control}
            render={({ field }) => (
              <select {...field} className="w-full px-3 py-2 border rounded-md">
                <option value="low">Низкий</option>
                <option value="medium">Средний</option>
                <option value="high">Высокий</option>
                <option value="urgent">Срочный</option>
              </select>
            )}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Желаемая дата выполнения</label>
          <Controller
            name="desired_completion_date"
            control={control}
            render={({ field }) => (
              <input
                {...field}
                type="date"
                className="w-full px-3 py-2 border rounded-md"
              />
            )}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Срок выполнения</label>
          <Controller
            name="deadline"
            control={control}
            render={({ field }) => (
              <input {...field} type="date" className="w-full px-3 py-2 border rounded-md" />
            )}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Сметная стоимость</label>
          <Controller
            name="estimated_cost"
            control={control}
            render={({ field }) => (
              <input
                {...field}
                type="number"
                min="0"
                className="w-full px-3 py-2 border rounded-md"
                placeholder="0.00"
              />
            )}
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Создание...' : 'Создать заявку'}
      </button>
    </form>
  );
};

export default RepairForm;
