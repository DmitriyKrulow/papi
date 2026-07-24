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
          className="text-blue-600 hover:text-blue-800 transition"
        >
          ← Назад
        </button>
        <h1 className="text-2xl font-bold text-gray-800">Новый актив</h1>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <AddAssetForm
          onSubmit={handleSubmit}
          onClose={() => navigate('/assets')}
        />
      </div>
    </div>
  );
};

export default AssetCreate;