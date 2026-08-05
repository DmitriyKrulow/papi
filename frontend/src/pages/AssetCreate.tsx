// frontend/src/pages/AssetCreate.tsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AddAssetForm } from '../components/assets';
import { useAssets } from '../hooks/useAssets';
import toast from 'react-hot-toast';

const AssetCreate: React.FC = () => {
  const navigate = useNavigate();
  const { createAsset } = useAssets();

  const handleSubmit = async (data: any) => {
    try {
      await createAsset(data);
      toast.success('Актив успешно создан');
      navigate('/assets');
    } catch (error) {
      toast.error('Ошибка создания актива');
      console.error(error);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate('/assets')}
          className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition"
        >
          ← Назад
        </button>
        <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Новый актив</h1>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-100 dark:border-gray-700 p-6">
        <AddAssetForm
          onSubmit={handleSubmit}
          onClose={() => navigate('/assets')}
        />
      </div>
    </div>
  );
};

export default AssetCreate;