// frontend/src/components/assets/AssetDetailsModal.tsx
import React from 'react';
import { Calendar, DollarSign, Edit, Trash2, MapPin, User } from 'lucide-react';
import type { Asset } from '../../types';
import { AssetStatusMap } from '../../types';
import { formatMoney, formatDate } from '../../utils/helpers';

interface AssetDetailsModalProps {
  asset: Asset | null;
  onClose: () => void;
  onEdit: (asset: Asset) => void;
  onDelete: (id: number) => void;
}

const AssetDetailsModal: React.FC<AssetDetailsModalProps> = ({ asset, onClose, onEdit, onDelete }) => {
  if (!asset) return null;

  const statusInfo = AssetStatusMap[asset.status];

  const getStatusColor = (color: string): string => {
    const colors: Record<string, string> = {
      green: 'bg-green-100 text-green-700',
      yellow: 'bg-yellow-100 text-yellow-700',
      blue: 'bg-blue-100 text-blue-700',
      gray: 'bg-gray-100 text-gray-700',
      red: 'bg-red-100 text-red-700',
    };
    return colors[color] || 'bg-gray-100 text-gray-700';
  };

  const DetailRow = ({ label, value, icon: Icon }: { label: string; value?: string | number; icon?: any }) => (
    <div className="flex items-start space-x-3 py-3 border-b border-gray-100 last:border-0">
      {Icon && <Icon className="w-5 h-5 text-gray-400 mt-0.5" />}
      <div>
        <p className="text-xs text-gray-500 uppercase">{label}</p>
        <p className="text-sm text-gray-800 mt-0.5">{value || <span className="text-gray-400 italic">Не указано</span>}</p>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <h3 className="text-2xl font-bold text-gray-800">{asset.name}</h3>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(statusInfo?.color || 'gray')}`}>
              {statusInfo?.label || asset.status}
            </span>
          </div>
          <p className="text-lg text-gray-600 font-mono">#{asset.inventory_number}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => onEdit(asset)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            <Edit className="w-4 h-4" />
            Редактировать
          </button>
          <button
            onClick={() => onDelete(asset.id)}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
          >
            <Trash2 className="w-4 h-4" />
            Удалить
          </button>
        </div>
      </div>

      <div className="bg-gray-50 rounded-lg p-6 space-y-4">
        <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Информация</h4>
        <DetailRow label="Инвентарный номер" value={asset.inventory_number} />
        <DetailRow label="Название" value={asset.name} />
        <DetailRow label="Описание" value={asset.description} />
        <DetailRow label="Модель" value={asset.model} />
        <DetailRow label="Производитель" value={asset.manufacturer_name} />
        <DetailRow label="Код производителя" value={asset.manufacturer_code} />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-gray-50 rounded-lg p-6 space-y-4">
          <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide flex items-center gap-2">
            <DollarSign className="w-4 h-4" /> Финансы
          </h4>
          <DetailRow label="Стоимость покупки" value={formatMoney(asset.purchase_price)} />
          <DetailRow label="Текущая стоимость" value={formatMoney(asset.current_value)} />
        </div>

        <div className="bg-gray-50 rounded-lg p-6 space-y-4">
          <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide flex items-center gap-2">
            <Calendar className="w-4 h-4" /> Дата
          </h4>
          <DetailRow label="Создан" value={formatDate(asset.created_at)} />
          <DetailRow label="Обновлен" value={formatDate(asset.updated_at)} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-gray-50 rounded-lg p-6 space-y-4">
          <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide flex items-center gap-2">
            <MapPin className="w-4 h-4" /> Местоположение
          </h4>
          <DetailRow label="Адрес" value={asset.location_address} />
          <DetailRow label="Подразделение" value={asset.department_code} />
        </div>

        <div className="bg-gray-50 rounded-lg p-6 space-y-4">
          <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide flex items-center gap-2">
            <User className="w-4 h-4" /> Ответственность
          </h4>
          <DetailRow label="Ответственное лицо" value={asset.responsible_person} />
        </div>
      </div>
    </div>
  );
};

export default AssetDetailsModal;
