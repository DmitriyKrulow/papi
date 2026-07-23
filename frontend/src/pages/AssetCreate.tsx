import React from 'react';
import { useNavigate } from 'react-router-dom';
import AssetForm from '../components/forms/AssetForm';
import { useAssets } from '../hooks/useAssets';

const AssetCreate: React.FC = () => {
  const navigate = useNavigate();
  const { createAsset, loading, error } = useAssets();

  const handleSubmit = async (data: any) => {
    try {
      await createAsset(data);
      navigate('/assets');
    } catch (err) {
      console.error('Failed to create asset:', err);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="flex items-center mb-6">
        <button
          onClick={() => navigate('/assets')}
          className="mr-4 text-blue-600 hover:text-blue-800"
        >
          ← Назад
        </button>
        <h1 className="text-3xl font-bold text-gray-900">Новый актив</h1>
      </div>

      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <AssetForm onSubmit={handleSubmit} loading={loading} />
          {error && (
            <div className="mt-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
              {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AssetCreate;
