import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useRepairs } from '../hooks/useRepairs';
import { useAssets } from '../hooks/useAssets';
import { useAuth } from '../hooks/useAuth';
import { UserRole } from '../domain/roles';
import { RepairStatusMap, PriorityMap } from '../types';

const RepairEdit: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const repairId = Number(id);
  const { repairs, loading, updateRepair, updateRepairStatus, updateRepairPriority } = useRepairs();
  const repair = repairs.find((r) => r.id === repairId);
  const { assets } = useAssets();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('');
  const [status, setStatus] = useState('');

  const [desiredCompletionDate, setDesiredCompletionDate] = useState('');
  const [deadline, setDeadline] = useState('');
  const [estimatedCost, setEstimatedCost] = useState('');
  const [saving, setSaving] = useState(false);
  const [assetId, setAssetId] = useState<number | undefined>(undefined);

  useEffect(() => {
    if (repair) {
      setTitle(repair.title);
      setDescription(repair.description);
      setPriority(repair.priority);
      setStatus(repair.status);
      setAssetId(repair.asset_id);
      if (repair.desired_completion_date) {
        setDesiredCompletionDate(new Date(repair.desired_completion_date).toISOString().split('T')[0]);
      }
      if (repair.deadline) {
        setDeadline(new Date(repair.deadline).toISOString().split('T')[0]);
      }
      if (repair.estimated_cost !== null && repair.estimated_cost !== undefined) {
        setEstimatedCost(repair.estimated_cost.toString());
      }
    }
  }, [repair]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await updateRepair(repairId, {
        title,
        description,
        priority: priority as any,
        desired_completion_date: desiredCompletionDate
          ? new Date(desiredCompletionDate).toISOString()
          : undefined,
        deadline: deadline ? new Date(deadline).toISOString() : undefined,
        estimated_cost: estimatedCost ? Number(estimatedCost) : undefined,
      });
      navigate(`/repairs/${repairId}`);
    } catch (error) {
      console.error('Failed to update repair:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleStatusChange = async (newStatus: string) => {
    try {
      await updateRepairStatus(repairId, newStatus);
      setStatus(newStatus);
    } catch (error) {
      console.error('Failed to update status:', error);
    }
  };

  const handlePriorityChange = async (newPriority: string) => {
    try {
      await updateRepairPriority(repairId, newPriority);
      setPriority(newPriority);
    } catch (error) {
      console.error('Failed to update priority:', error);
    }
  };

  if (loading) {
    return <div>Загрузка...</div>;
  }

  if (!repair) {
    return <div className="text-red-500">Заявка не найдена</div>;
  }

  const templateOptions = [
    {
      id: 'template_electrical',
      title: 'Электрические проблемы',
      description: 'Проблемы с электрическими цепями, проводкой, розетками',
    },
    {
      id: 'template_mechanical',
      title: 'Механические повреждения',
      description: 'Износ механизмов, шум, вибрация, скрипы',
    },
    {
      id: 'template_software',
      title: 'Проблемы ПО',
      description: 'Сбои в программном обеспечении, обновления',
    },
    {
      id: 'template_network',
      title: 'Сетевые проблемы',
      description: 'Проблемы с сетевым подключением, маршрутизацией',
    },
  ];

  const applyTemplate = (template: typeof templateOptions[0]) => {
    const filled = {
      title: `${template.title} - ${repair.asset_id ? `Актив ID: ${repair.asset_id}` : ''}`,
      description: `${template.description}\n\nАктив ID: ${repair.asset_id}\nТекущее описание:\n${description}\n\nОбновленная информация о проблеме:`,
    };
    setTitle(filled.title);
    setDescription(filled.description);
  };

  const asset = assets.find((a) => a.id === repair.asset_id);

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Редактирование заявки #{repairId}</h1>
        <div className="mt-2 flex flex-wrap gap-2">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${RepairStatusMap[repair.status as keyof typeof RepairStatusMap].color === 'green' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' : repair.status === 'rejected' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300' : repair.status === 'in_progress' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300' : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'}`}>
            {RepairStatusMap[repair.status as keyof typeof RepairStatusMap].label}
          </span>
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${PriorityMap[repair.priority as keyof typeof PriorityMap].color === 'red' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300' : PriorityMap[repair.priority as keyof typeof PriorityMap].color === 'orange' ? 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300' : PriorityMap[repair.priority as keyof typeof PriorityMap].color === 'blue' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300' : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'}`}>
            {PriorityMap[repair.priority as keyof typeof PriorityMap].label}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 border border-gray-100 dark:border-gray-700">
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">Шаблоны заявок</label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {templateOptions.map((template) => (
                  <button
                    key={template.id}
                    onClick={() => applyTemplate(template)}
                    className="text-left p-4 border border-gray-200 dark:border-gray-600 rounded-lg hover:border-blue-500 dark:hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                  >
                    <h3 className="font-medium text-blue-600 dark:text-blue-400">{template.title}</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{template.description}</p>
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Название</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                  placeholder="Краткое описание проблемы"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Описание</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                  rows={4}
                  placeholder="Подробное описание неисправности"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Приоритет</label>
                  <select
                    value={priority}
                    onChange={(e) => handlePriorityChange(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                  >
                    <option value="low">Низкий</option>
                    <option value="medium">Средний</option>
                    <option value="high">Высокий</option>
                    <option value="urgent">Срочный</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Статус</label>
                  <select
                    value={status}
                    onChange={(e) => handleStatusChange(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                  >
                    <option value="draft">Черновик</option>
                    <option value="submitted">Подана</option>
                    <option value="approved">Одобрена</option>
                    <option value="in_progress">В работе</option>
                    <option value="completed">Выполнена</option>
                    <option value="rejected">Отклонена</option>
                    <option value="cancelled">Отменена</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Желаемая дата выполнения</label>
                  <input
                    type="date"
                    value={desiredCompletionDate}
                    onChange={(e) => setDesiredCompletionDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Срок выполнения</label>
                  <input
                    type="date"
                    value={deadline}
                    onChange={(e) => setDeadline(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Сметная стоимость</label>
                  <input
                    type="number"
                    value={estimatedCost}
                    onChange={(e) => setEstimatedCost(e.target.value)}
                    min="0"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                    placeholder="0.00"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={saving}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? 'Сохранение...' : 'Сохранить изменения'}
              </button>
            </form>
          </div>
        </div>

        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 border border-gray-100 dark:border-gray-700">
            <h2 className="text-lg font-medium mb-4 text-gray-900 dark:text-gray-100">Информация о заявке</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Актив</label>
                <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                  {asset ? `${asset.name} (ID: ${asset.id})` : `Актив ID: ${repair.asset_id}`}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Создано</label>
                <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                  {new Date(repair.created_at).toLocaleDateString('ru-RU')}
                </p>
              </div>

              {repair.created_by && (
                <div>
                  <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Автор</label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">{repair.created_by}</p>
                </div>
              )}

              {repair.assigned_to && (
                <div>
                  <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Исполнитель</label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">{repair.assigned_to}</p>
                </div>
              )}

              {repair.estimated_cost !== undefined && (
                <div>
                  <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Сметная стоимость</label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                    {new Intl.NumberFormat('ru-RU', {
                      style: 'currency',
                      currency: 'RUB',
                    }).format(Number(repair.estimated_cost))}
                  </p>
                </div>
              )}

              {repair.actual_cost !== undefined && (
                <div>
                  <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Фактическая стоимость</label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                    {new Intl.NumberFormat('ru-RU', {
                      style: 'currency',
                      currency: 'RUB',
                    }).format(Number(repair.actual_cost))}
                  </p>
                </div>
              )}

              {repair.completion_notes && (
                <div>
                  <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Заметки о выполнении</label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">{repair.completion_notes}</p>
                </div>
              )}

              {repair.rejection_reason && (
                <div>
                  <label className="block text-sm font-medium text-gray-500 dark:text-gray-400">Причина отклонения</label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">{repair.rejection_reason}</p>
                </div>
              )}
            </div>

            {user?.role === UserRole.ADMIN && (
              <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">Действия администратора</h3>
                <div className="space-y-2">
                  <button
                    onClick={() => handleStatusChange('approved')}
                    className="w-full px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm"
                  >
                    Одобрить
                  </button>
                  <button
                    onClick={() => handleStatusChange('in_progress')}
                    className="w-full px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                  >
                    Начать выполнение
                  </button>
                  <button
                    onClick={() => handleStatusChange('completed')}
                    className="w-full px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 text-sm"
                  >
                    Завершить
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RepairEdit;
