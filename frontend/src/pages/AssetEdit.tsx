import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import AssetForm from '../components/forms/AssetForm';
import { useAssets } from '../hooks/useAssets';

const AssetEdit: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { assets, loading, updateAsset, error } = useAssets();
  const [asset, setAsset] = useState<any>(null);
  const [formData, setFormData] = useState<any>(null);

  useEffect(() => {
    if (!loading && assets.length > 0) {
      const found = assets.find((a) => a.id === parseInt(id || '0'));
      if (found) {
        setAsset(found);
        setFormData({
          inventory_number: found.inventory_number,
          name: found.name,
          description: found.description || '',
          model: found.model || '',
          manufacturer_code: found.manufacturer_code || '',
          manufacturer_name: found.manufacturer_name || '',
          country_of_origin: found.country_of_origin || '',
          accounting_code: found.accounting_code || '',
          department_code: found.department_code || '',
          responsible_person: found.responsible_person || '',
          purchase_price: found.purchase_price || 0,
          current_value: found.current_value || 0,
          residual_value: found.residual_value || 0,
          depreciation_rate: found.depreciation_rate || 0,
          location: found.location || '',
          location_address: found.location_address || '',
          responsible_phone: found.responsible_phone || '',
          purchase_date: found.purchase_date || '',
          commissioning_date: found.commissioning_date || '',
          warranty_expiry: found.warranty_expiry || '',
          last_maintenance_date: found.last_maintenance_date || '',
          next_maintenance_date: found.next_maintenance_date || '',
          decommissioning_date: found.decommissioning_date || '',
          tags: found.tags || [],
          notes: found.notes || '',
          is_active: found.is_active,
        });
      } else {
        navigate('/assets');
      }
    }
  }, [assets, loading, id, navigate]);

  const handleSubmit = async (data: any) => {
    try {
      await updateAsset(parseInt(id || '0'), data);
      navigate(`/assets/${id}`);
    } catch (err) {
      console.error('Failed to update asset:', err);
    }
  };

  if (loading) return <div>Загрузка...</div>;
  if (error) return <div className="text-red-500">Ошибка: {error}</div>;
  if (!asset || !formData) return <div>Актив не найден</div>;

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="flex items-center mb-6">
        <button
          onClick={() => navigate(`/assets/${id}`)}
          className="mr-4 text-blue-600 hover:text-blue-800"
        >
          ← Назад
        </button>
        <h1 className="text-3xl font-bold text-gray-900">
          Редактирование актива: {asset.name}
        </h1>
      </div>

      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <AssetForm onSubmit={handleSubmit} defaultValue={formData} loading={loading} />
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

export default AssetEdit;
