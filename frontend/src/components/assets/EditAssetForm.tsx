// frontend/src/components/assets/EditAssetForm.tsx
import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import type { Asset, AssetTypeConfig } from '../../types';
import { AssetTypeNames, MaintenanceEventTypes } from '../../types';

interface EditAssetFormProps {
  existingAsset: Asset;
  onSubmit: (data: Asset) => Promise<void>;
  onClose: () => void;
}

interface FormData {
  inventory_number: string;
  name: string;
  description?: string;
  model?: string;
  manufacturer_code?: string;
  manufacturer_name?: string;
  asset_type?: string;
  purchase_price?: number;
  current_value?: number;
  status: string;
  location_address?: string;
  responsible_person?: string;
  department_code?: string;
  purchase_date?: string;
  commissioning_date?: string;
  warranty_expiry?: string;
  serial_number?: string;
  capacity?: number;
  power?: string;
  weight?: string;
  consumable_type?: string;
  crypto_wallet_address?: string;
  crypto_token_symbol?: string;
  depreciation_years?: number;
  next_maintenance_date?: string;
}

const EditAssetForm: React.FC<EditAssetFormProps> = ({ existingAsset, onSubmit, onClose }) => {
  const [assetTypes, setAssetTypes] = useState<AssetTypeConfig[]>([]);
  const [selectedType, setSelectedType] = useState<string>(existingAsset.asset_type || '');

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<FormData>({
    defaultValues: {
      inventory_number: existingAsset.inventory_number,
      name: existingAsset.name,
      description: existingAsset.description || '',
      model: existingAsset.model || '',
      manufacturer_code: existingAsset.manufacturer_code || '',
      manufacturer_name: existingAsset.manufacturer_name || '',
      asset_type: existingAsset.asset_type || '',
      purchase_price: existingAsset.purchase_price || 0,
      current_value: existingAsset.current_value || 0,
      status: existingAsset.status,
      location_address: existingAsset.location_address || '',
      responsible_person: existingAsset.responsible_person || '',
      department_code: existingAsset.department_code || '',
      purchase_date: existingAsset.purchase_date || '',
      commissioning_date: existingAsset.commissioning_date || '',
      warranty_expiry: existingAsset.warranty_expiry || '',
      serial_number: existingAsset.serial_number || '',
      capacity: existingAsset.capacity || undefined,
      power: existingAsset.power || '',
      weight: existingAsset.weight || '',
      consumable_type: existingAsset.consumable_type || '',
      crypto_wallet_address: existingAsset.crypto_wallet_address || '',
      crypto_token_symbol: existingAsset.crypto_token_symbol || '',
      depreciation_years: existingAsset.depreciation_years || undefined,
      next_maintenance_date: existingAsset.next_maintenance_date || '',
    },
  });

  const watchAssetType = watch('asset_type');

  useEffect(() => {
    fetch('/api/asset-types/')
      .then(r => r.json())
      .then(setAssetTypes)
      .catch(console.error);
  }, []);

  useEffect(() => {
    const initialType = existingAsset.asset_type || '';
    setSelectedType(initialType);
    if (initialType) {
      const typeConfig = assetTypes.find(t => t.code === initialType);
      if (typeConfig && typeConfig.default_depreciation_years) {
        setValue('depreciation_years', typeConfig.default_depreciation_years);
      }
    }
  }, []);

  useEffect(() => {
    if (watchAssetType) {
      setSelectedType(watchAssetType);
      const typeConfig = assetTypes.find(t => t.code === watchAssetType);
      if (typeConfig && typeConfig.default_depreciation_years) {
        setValue('depreciation_years', typeConfig.default_depreciation_years);
      }
    }
  }, [watchAssetType, assetTypes]);

  const handleSubmitForm = async (data: FormData) => {
    try {
      await onSubmit({
        ...existingAsset,
        inventory_number: data.inventory_number,
        name: data.name,
        description: data.description,
        model: data.model,
        manufacturer_code: data.manufacturer_code,
        manufacturer_name: data.manufacturer_name,
        asset_type: data.asset_type,
        purchase_price: data.purchase_price ? Number(data.purchase_price) : undefined,
        current_value: data.current_value ? Number(data.current_value) : undefined,
        status: data.status as Asset['status'],
        location_address: data.location_address,
        responsible_person: data.responsible_person,
        department_code: data.department_code,
        purchase_date: data.purchase_date,
        commissioning_date: data.commissioning_date,
        warranty_expiry: data.warranty_expiry,
        serial_number: data.serial_number,
        capacity: data.capacity ? Number(data.capacity) : undefined,
        power: data.power,
        weight: data.weight,
        consumable_type: data.consumable_type,
        crypto_wallet_address: data.crypto_wallet_address,
        crypto_token_symbol: data.crypto_token_symbol,
        depreciation_years: data.depreciation_years ? Number(data.depreciation_years) : undefined,
        next_maintenance_date: data.next_maintenance_date,
      });
    } catch (error) {
      console.error('Ошибка отправки формы:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit(handleSubmitForm)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Инвентарный номер *
          </label>
          <input
            type="text"
            {...register('inventory_number', {
              required: 'Обязательное поле',
              minLength: {
                value: 3,
                message: 'Минимум 3 символа',
              },
            })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="INV-001"
          />
          {errors.inventory_number && (
            <p className="mt-1 text-sm text-red-600">{errors.inventory_number.message}</p>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Название *
          </label>
          <input
            type="text"
            {...register('name', {
              required: 'Обязательное поле',
              minLength: {
                value: 2,
                message: 'Минимум 2 символа',
              },
            })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Название актива"
          />
            {errors.name && (
              <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Тип актива
            </label>
            <select
              {...register('asset_type')}
              onChange={(e) => {
                register('asset_type').onChange(e);
                setSelectedType(e.target.value);
                const typeConfig = assetTypes.find(t => t.code === e.target.value);
                if (typeConfig && typeConfig.default_depreciation_years && !existingAsset.depreciation_years) {
                  setValue('depreciation_years', typeConfig.default_depreciation_years);
                }
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Не выбран</option>
              {assetTypes.map((type) => (
                <option key={type.code} value={type.code}>
                  {type.icon} {type.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Срок амортизации (лет)
            </label>
            <input
              type="number"
              min="1"
              {...register('depreciation_years', {
                valueAsNumber: true,
              })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="5"
            />
          </div>
        </div>

        {selectedType === 'fire_extinguisher' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Объём (л)
              </label>
              <input
                type="number"
                step="0.1"
                {...register('capacity', { valueAsNumber: true })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Следующая проверка
              </label>
              <input
                type="date"
                {...register('next_maintenance_date')}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        )}

        {(selectedType === 'computer' || selectedType === 'printer') && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Серийный номер
              </label>
              <input
                type="text"
                {...register('serial_number')}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="SN-12345"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Мощность (Вт)
              </label>
              <input
                type="text"
                {...register('power')}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="300"
              />
            </div>
          </div>
        )}

        {selectedType === 'printer' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Тип тонера
              </label>
              <input
                type="text"
                {...register('consumable_type')}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="CF280A"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Следующее обслуживание
              </label>
              <input
                type="date"
                {...register('next_maintenance_date')}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        )}

        {selectedType === 'crypto_token' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Имя пользователя / Логин
              </label>
              <input
                type="text"
                {...register('crypto_wallet_address')}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="ivanov.a"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Серийный номер / Идентификатор
              </label>
              <input
                type="text"
                {...register('crypto_token_symbol')}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="SN-XXXXX"
              />
            </div>
          </div>
        )}

        {selectedType === 'consumables' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Тип расходника
              </label>
              <input
                type="text"
                {...register('consumable_type')}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Бумага А4"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Вес (кг)
              </label>
              <input
                type="text"
                {...register('weight')}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="1.5"
              />
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Дата покупки
            </label>
            <input
              type="date"
              {...register('purchase_date')}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Гарантия до
            </label>
            <input
              type="date"
              {...register('warranty_expiry')}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Модель
            </label>
          <input
            type="text"
            {...register('model')}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Модель"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Код производителя
          </label>
          <input
            type="text"
            {...register('manufacturer_code')}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Код производителя"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Производитель
        </label>
        <input
          type="text"
          {...register('manufacturer_name')}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Производитель"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Стоимость покупки (₽)
          </label>
          <input
            type="number"
            step="0.01"
            min="0"
            {...register('purchase_price', {
              valueAsNumber: true,
            })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="0.00"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Текущая стоимость (₽)
          </label>
          <input
            type="number"
            step="0.01"
            min="0"
            {...register('current_value', {
              valueAsNumber: true,
            })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="0.00"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Статус *
        </label>
        <select
          {...register('status', {
            required: 'Обязательное поле',
          })}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="active">Активен</option>
          <option value="maintenance">На ремонте</option>
          <option value="reserved">В резерве</option>
          <option value="decommissioned">Выведен</option>
          <option value="lost">Утерян</option>
          <option value="written_off">Списан</option>
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Адрес расположения
          </label>
          <input
            type="text"
            {...register('location_address')}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Адрес"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Ответственное лицо
          </label>
          <input
            type="text"
            {...register('responsible_person')}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="ФИО"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Код подразделения
        </label>
        <input
          type="text"
          {...register('department_code')}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Деп-001"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Описание
        </label>
        <textarea
          {...register('description')}
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Описание актива..."
        />
      </div>

      <div className="flex gap-3 pt-4">
        <button
          type="button"
          onClick={onClose}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition text-gray-700"
        >
          Отмена
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              Сохранение...
            </>
          ) : (
            'Сохранить'
          )}
        </button>
      </div>
    </form>
  );
};

export default EditAssetForm;
