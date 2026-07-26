import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useRepairs } from '../hooks/useRepairs';
import { useAssets } from '../hooks/useAssets';
import { useAuth } from '../hooks/useAuth';
import RepairForm from '../components/forms/RepairForm';

const RepairCreate: React.FC = () => {
  const { createRepair, loading } = useRepairs();
  const { assets, loading: assetsLoading, fetchAssets } = useAssets();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [selectedAssetId, setSelectedAssetId] = useState<number | ''>('');
  const [formTemplateData, setFormTemplateData] = useState<{ title: string; description: string } | null>(null);
  
  const applyTemplateRef = useRef<(title: string, description: string) => void | null>(null);
  
  console.log('[RepairCreate] Component rendered');

  const handleSubmit = async (data: any) => {
    console.log('[RepairCreate] handleSubmit called with:', data);
    console.log('[RepairCreate] selectedAssetId:', selectedAssetId);
    console.log('[RepairCreate] formTemplateData:', formTemplateData);
    try {
      const assetId = selectedAssetId ? Number(selectedAssetId) : (data.asset_id || 0);
      console.log('[RepairCreate] final assetId:', assetId);
      if (!assetId) {
        alert('Пожалуйста, выберите актив');
        return;
      }
      const formData: any = {
        asset_id: assetId,
        title: data.title || formTemplateData?.title || '',
        description: data.description || formTemplateData?.description || '',
        priority: data.priority || 'medium',
        created_by: user?.id || 0,
      };
      
      if (data.desired_completion_date) {
        formData.desired_completion_date = new Date(data.desired_completion_date).toISOString();
      }
      
      if (data.deadline) {
        formData.deadline = new Date(data.deadline).toISOString();
      }
      
      if (data.estimated_cost && Number(data.estimated_cost) > 0) {
        formData.estimated_cost = Number(data.estimated_cost);
      }
      
      await createRepair(formData);
      // Обновляем активы после создания заявки
      await fetchAssets();
      navigate('/repairs');
    } catch (error) {
      console.error('Failed to create repair:', error);
      alert('Ошибка при создании заявки. Проверьте консоль для подробной информации.');
    }
  };

  const applyTemplateToForm = useCallback((template: typeof templateOptions[0]) => {
    const asset = assets.find((a) => a.id === Number(selectedAssetId));
    const assetInfo = asset ? `Актив: ${asset.name} (ID: ${asset.id})` : '';
    
    const title = `${template.title}${assetInfo ? ' - ' + assetInfo : ''}`;
    const description = `${template.description}\n\n${assetInfo}\n\nДополнительная информация о проблеме:`;
    
    setFormTemplateData({ title, description });
  }, [assets, selectedAssetId]);

  if (assetsLoading) {
    return <div>Загрузка...</div>;
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

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Новая заявка на ремонт</h1>
        <p className="mt-2 text-sm text-gray-600">
          Создайте заявку на ремонт оборудования или систем
        </p>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Шаблоны заявок</label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {templateOptions.map((template) => (
              <button
                key={template.id}
                onClick={() => applyTemplateToForm(template)}
                className="text-left p-4 border rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
              >
                <h3 className="font-medium text-blue-600">{template.title}</h3>
                <p className="text-sm text-gray-600 mt-1">{template.description}</p>
              </button>
            ))}
          </div>
        </div>

        <RepairForm
          onSubmit={handleSubmit}
          loading={loading}
          assetId={Number(selectedAssetId) || undefined}
          assets={assets}
          defaultValue={formTemplateData || undefined}
        />

        <div className="mt-6">
          <label className="block text-sm font-medium mb-2">Выберите актив</label>
          <select
            value={selectedAssetId}
            onChange={(e) => setSelectedAssetId(e.target.value ? Number(e.target.value) : '')}
            className="w-full px-3 py-2 border rounded-md"
          >
            <option value="">-- Выберите актив --</option>
            {assets.map((asset) => (
              <option key={asset.id} value={asset.id}>
                {asset.name} (ID: {asset.id} - {asset.inventory_number})
              </option>
            ))}
          </select>
          <p className="mt-2 text-sm text-gray-500">
            Выбор актива поможет автоматически заполнить информацию о ремонтируемом оборудовании
          </p>
        </div>
      </div>
    </div>
  );
};

export default RepairCreate;
