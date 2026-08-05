import React, { useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

interface Asset {
  id: number;
  name: string;
  inventory_number: string;
}

interface RepairFormProps {
  onSubmit: (data: RepairFormData) => void;
  defaultValue?: Partial<RepairFormData>;
  loading?: boolean;
  assetId?: number;
  assets?: Asset[];
  onApplyTemplate?: (title: string, description: string) => void;
}

const repairSchema = z.object({
  title: z.string().min(1, { message: 'Обязательное поле' }).max(255, 'Максимум 255 символов'),
  description: z.string().min(1, { message: 'Обязательное поле' }),
  asset_id: z.number().int().positive('ID актива должен быть больше 0'),
  priority: z.enum(['low', 'medium', 'high', 'urgent'] as const, { message: 'Некорректный приоритет' }),
  created_by: z.number().int().optional(),
  desired_completion_date: z.string().optional(),
  deadline: z.string().optional(),
  estimated_cost: z.number().min(0, { message: 'Не может быть отрицательным' }).optional(),
});

type RepairFormData = z.infer<typeof repairSchema>;

const RepairForm: React.FC<RepairFormProps> = ({
  onSubmit,
  defaultValue,
  loading = false,
  assetId,
  assets = [],
  onApplyTemplate,
}) => {
  const {
    control,
    handleSubmit,
    formState: { errors },
    setValue,
  } = useForm<RepairFormData>({
    resolver: zodResolver(repairSchema),
    defaultValues: {
      title: '',
      description: '',
      priority: 'medium',
      asset_id: assetId || undefined,
      desired_completion_date: '',
      deadline: '',
      estimated_cost: undefined,
    },
  });

  const handleApplyTemplate = (templateTitle: string, templateDescription: string) => {
    setValue('title', templateTitle, { shouldValidate: true });
    setValue('description', templateDescription, { shouldValidate: true });
    onApplyTemplate?.(templateTitle, templateDescription);
  };

  console.log('[RepairForm] Component rendered');
  console.log('[RepairForm] assetId:', assetId);
  console.log('[RepairForm] defaultValue:', defaultValue);
  console.log('[RepairForm] formState errors:', errors);

  useEffect(() => {
    if (assetId) {
      console.log('[RepairForm] assetId changed to:', assetId);
      setValue('asset_id', assetId, { shouldValidate: true });
    }
  }, [assetId, setValue]);

  useEffect(() => {
    if (defaultValue?.title) {
      console.log('[RepairForm] defaultValue.title changed to:', defaultValue.title);
      setValue('title', defaultValue.title, { shouldValidate: true });
    }
    if (defaultValue?.description) {
      console.log('[RepairForm] defaultValue.description changed to:', defaultValue.description);
      setValue('description', defaultValue.description, { shouldValidate: true });
    }
  }, [defaultValue, setValue]);

  const handleFormSubmit = (data: any) => {
    console.log('[RepairForm] handleFormSubmit called with:', data);
    return onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-1">Название</label>
        <Controller
          name="title"
          control={control}
          render={({ field }) => (
            <input
              {...field}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              placeholder="Краткое описание проблемы"
              readOnly={!!defaultValue?.title}
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
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              rows={4}
              placeholder="Подробное описание неисправности"
              readOnly={!!defaultValue?.description}
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
              <select {...field} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100">
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
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
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
              <input {...field} type="date" className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" />
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
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
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
