// frontend/src/components/assets/AssetDetailsModal.tsx
import React, { useState, useEffect } from 'react';
import { Calendar, DollarSign, Edit, Trash2, MapPin, User, Wrench, Plus, RefreshCw, Image } from 'lucide-react';
import type { Asset, MaintenanceEvent } from '../../types';
import { AssetStatusMap, MaintenanceEventTypes, AssetTypeNames } from '../../types';
import { formatMoney, formatDate } from '../../utils/helpers';
import toast from 'react-hot-toast';
import AssetPhotoGallery from './AssetPhotoGallery';
import AssetDocuments from './AssetDocuments';

interface AssetDetailsModalProps {
  asset: Asset | null;
  onClose: () => void;
  onEdit: (asset: Asset) => void;
  onDelete: (id: number) => void;
  onHardDelete?: (id: number) => void;
  onRestore?: (id: number) => void;
}

const AssetDetailsModal: React.FC<AssetDetailsModalProps> = ({ asset, onClose, onEdit, onDelete, onHardDelete, onRestore }) => {
  const [maintenanceEvents, setMaintenanceEvents] = useState<MaintenanceEvent[]>([]);
  const [repairHistory, setRepairHistory] = useState<any[]>([]);
  const [showAddEvent, setShowAddEvent] = useState(false);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [loadingRepairs, setLoadingRepairs] = useState(false);
  const [isGalleryOpen, setIsGalleryOpen] = useState(false);
  const [newEvent, setNewEvent] = useState({
    event_type: 'repair',
    event_date: new Date().toISOString().split('T')[0],
    description: '',
    cost: '',
    performed_by: '',
    result: '',
  });

  const eventTypeOptions = Object.entries(MaintenanceEventTypes);

  const fetchMaintenanceEvents = async () => {
    if (!asset) return;
    setLoadingEvents(true);
    try {
      const res = await fetch(`/api/maintenance-events/asset/${asset.id}`);
      if (res.ok) {
        const data = await res.json();
        setMaintenanceEvents(data.items || []);
      }
    } catch (err) {
      console.error('Ошибка загрузки событий:', err);
    } finally {
      setLoadingEvents(false);
    }
  };

useEffect(() => {
    fetchMaintenanceEvents();
    fetchRepairHistory();
  }, [asset?.id]);

  const fetchRepairHistory = async () => {
    if (!asset) return;
    setLoadingRepairs(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/assets/${asset.id}/repair-history`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setRepairHistory(data.items || []);
      }
    } catch (err) {
      console.error('Ошибка загрузки истории ремонтов:', err);
    } finally {
      setLoadingRepairs(false);
    }
  };

  const handleAddEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!asset) return;
    try {
      const res = await fetch(`/api/maintenance-events/asset/${asset.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...newEvent, cost: newEvent.cost ? parseFloat(newEvent.cost) : undefined }),
      });
      if (res.ok) {
        toast.success('Событие добавлено');
        setShowAddEvent(false);
        setNewEvent({
          event_type: 'repair',
          event_date: new Date().toISOString().split('T')[0],
          description: '',
          cost: '',
          performed_by: '',
          result: '',
        });
        fetchMaintenanceEvents();
      }
    } catch (err) {
      toast.error('Ошибка добавления события');
    }
  };

  if (!asset) return null;

  const assetTypeInfo = AssetTypeNames[asset.asset_type || ''];
  const statusInfo = AssetStatusMap[asset.status];

const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      green: 'bg-green-100 text-green-700',
      yellow: 'bg-yellow-100 text-yellow-700',
      blue: 'bg-blue-100 text-blue-700',
      gray: 'bg-gray-100 text-gray-700',
      red: 'bg-red-100 text-red-700',
      orange: 'bg-orange-100 text-orange-700',
    };
    return colors[status] || 'bg-gray-100 text-gray-700';
  };

  const getRepairStatusBadge = (status: string): { label: string; color: string } => {
    const map: Record<string, { label: string; color: string }> = {
      approved: { label: 'Одобрено', color: 'bg-blue-100 text-blue-700' },
      in_progress: { label: 'В работе', color: 'bg-yellow-100 text-yellow-700' },
      completed: { label: 'Завершено', color: 'bg-green-100 text-green-700' },
    };
    return map[status] || { label: status, color: 'bg-gray-100 text-gray-700' };
  };

  const getAssetTypeColor = (color: string): string => {
    const colors: Record<string, string> = {
      amber: 'bg-amber-100 text-amber-700',
      red: 'bg-red-100 text-red-700',
      orange: 'bg-orange-100 text-orange-700',
      blue: 'bg-blue-100 text-blue-700',
      gray: 'bg-gray-100 text-gray-700',
      green: 'bg-green-100 text-green-700',
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
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <h3 className="text-2xl font-bold text-gray-800">{asset.name}</h3>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(statusInfo?.color || 'gray')}`}>
              {statusInfo?.label || asset.status}
            </span>
            {!asset.is_active && (
              <span className="px-3 py-1 rounded-full text-sm font-medium bg-gray-200 text-gray-700">
                Скрыт
              </span>
            )}
            {assetTypeInfo && (
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getAssetTypeColor(assetTypeInfo.color)}`}>
                {assetTypeInfo.icon} {assetTypeInfo.label}
              </span>
            )}
          </div>
          <p className="text-lg text-gray-600 font-mono">#{asset.inventory_number}</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setIsGalleryOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 transition whitespace-nowrap"
          >
            <Image className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Фотографии</span>
            <span className="sm:hidden">📷</span>
          </button>
          {asset.is_active ? (
            <>
              <button
                onClick={() => onEdit(asset)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition whitespace-nowrap"
              >
                <Edit className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Редактировать</span>
                <span className="sm:hidden">✏️</span>
              </button>
              <button
                onClick={() => onDelete(asset.id)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 transition whitespace-nowrap"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Списать</span>
                <span className="sm:hidden">🗑️</span>
              </button>
            </>
          ) : (
            <>
              {onRestore && (
                <button
                  onClick={() => onRestore(asset.id)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 transition whitespace-nowrap"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Восстановить</span>
                  <span className="sm:hidden">🔄</span>
                </button>
              )}
              {onHardDelete && (
                <button
                  onClick={() => onHardDelete(asset.id)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-800 text-white text-sm rounded-lg hover:bg-red-900 transition whitespace-nowrap"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Удалить навсегда</span>
                  <span className="sm:hidden">💀</span>
                </button>
              )}
            </>
          )}
        </div>
      </div>

      <div className="bg-gray-50 rounded-lg p-6 space-y-4">
        <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Информация</h4>
        <DetailRow label="Инвентарный номер" value={asset.inventory_number} />
        <DetailRow label="Название" value={asset.name} />
        <DetailRow label="Описание" value={asset.description} />
        <DetailRow label="Модель" value={asset.model} />
        <DetailRow label="Тип актива" value={assetTypeInfo ? `${assetTypeInfo.icon} ${assetTypeInfo.label}` : asset.asset_type} />
        <DetailRow label="Производитель" value={asset.manufacturer_name} />
        <DetailRow label="Код производителя" value={asset.manufacturer_code} />
        {asset.serial_number && <DetailRow label="Серийный номер" value={asset.serial_number} />}
        {asset.depreciation_years && <DetailRow label="Срок амортизации" value={`${asset.depreciation_years} лет`} />}
        {asset.capacity && <DetailRow label="Объём" value={`${asset.capacity} л`} />}
        {asset.power && <DetailRow label="Мощность" value={`${asset.power} Вт`} />}
        {asset.consumable_type && <DetailRow label="Тип расходника" value={asset.consumable_type} />}
        {asset.crypto_wallet_address && <DetailRow label="Имя пользователя / Логин" value={asset.crypto_wallet_address} />}
        {asset.crypto_token_symbol && <DetailRow label="Серийный номер / Идентификатор" value={asset.crypto_token_symbol} />}
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
            <Calendar className="w-4 h-4" /> Даты
          </h4>
          <DetailRow label="Создан" value={formatDate(asset.created_at)} />
          <DetailRow label="Обновлен" value={formatDate(asset.updated_at)} />
          {asset.purchase_date && <DetailRow label="Дата покупки" value={formatDate(asset.purchase_date)} />}
          {asset.warranty_expiry && <DetailRow label="Гарантия до" value={formatDate(asset.warranty_expiry)} />}
          {asset.next_maintenance_date && <DetailRow label="Следующее обслуживание" value={formatDate(asset.next_maintenance_date)} />}
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

      <div className="bg-gray-50 rounded-lg p-6 space-y-4">
        <div className="flex justify-between items-center">
          <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide flex items-center gap-2">
            <Wrench className="w-4 h-4" /> История обслуживания
          </h4>
          <button
            onClick={() => setShowAddEvent(!showAddEvent)}
            className="flex items-center gap-1 px-3 py-1 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700 transition"
          >
            <Plus className="w-3 h-3" />
            Добавить
          </button>
        </div>

        {showAddEvent && (
          <form onSubmit={handleAddEvent} className="space-y-3 bg-white p-4 rounded-lg border">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Тип события</label>
                <select
                  value={newEvent.event_type}
                  onChange={e => setNewEvent({...newEvent, event_type: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                >
                  {eventTypeOptions.map(([key, val]) => (
                    <option key={key} value={key}>{val.icon} {val.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Дата</label>
                <input
                  type="date"
                  value={newEvent.event_date}
                  onChange={e => setNewEvent({...newEvent, event_date: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Выполнял</label>
                <input
                  type="text"
                  value={newEvent.performed_by}
                  onChange={e => setNewEvent({...newEvent, performed_by: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                  placeholder="ФИО"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Стоимость (₽)</label>
                <input
                  type="number"
                  step="0.01"
                  value={newEvent.cost}
                  onChange={e => setNewEvent({...newEvent, cost: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                  placeholder="0.00"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Описание</label>
              <textarea
                value={newEvent.description}
                onChange={e => setNewEvent({...newEvent, description: e.target.value})}
                rows={2}
                className="w-full px-3 py-2 border rounded-lg text-sm"
                placeholder="Описание работ..."
              />
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setShowAddEvent(false)}
                className="flex-1 px-3 py-2 border rounded-lg text-sm hover:bg-gray-50"
              >
                Отмена
              </button>
              <button
                type="submit"
                className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
              >
                Сохранить
              </button>
            </div>
          </form>
        )}

{loadingEvents ? (
          <p className="text-sm text-gray-500 text-center py-4">Загрузка...</p>
        ) : maintenanceEvents.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">Нет записей об обслуживании</p>
        ) : (
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {maintenanceEvents.map((event) => {
              const eventTypeInfo = MaintenanceEventTypes[event.event_type as keyof typeof MaintenanceEventTypes];
              return (
                <div key={event.id} className="bg-white p-3 rounded-lg border text-sm">
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-2">
                      <span>{eventTypeInfo?.icon || '🔧'}</span>
                      <span className="font-medium">{eventTypeInfo?.label || event.event_type}</span>
                    </div>
                    <span className="text-gray-500">{formatDate(event.event_date)}</span>
                  </div>
                  {event.description && <p className="mt-1 text-gray-600">{event.description}</p>}
                  <div className="mt-2 flex gap-3 text-xs text-gray-500">
                    {event.cost && <span>Стоимость: {formatMoney(event.cost)}</span>}
                    {event.performed_by && <span>Выполнил: {event.performed_by}</span>}
                    {event.result && <span>Результат: {event.result}</span>}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* История ремонтов из заявок */}
      {asset.is_active && (
        <div className="bg-gray-50 rounded-lg p-6 space-y-4">
          <div className="flex justify-between items-center">
            <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide flex items-center gap-2">
              <Wrench className="w-4 h-4" /> История ремонтов (заявки)
            </h4>
          </div>

          {loadingRepairs ? (
            <p className="text-sm text-gray-500 text-center py-4">Загрузка...</p>
          ) : repairHistory.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-4">Нет заявок на ремонт</p>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {repairHistory.map((repair: any) => {
                const badge = getRepairStatusBadge(repair.status);
                return (
                  <div key={repair.id} className="bg-white p-3 rounded-lg border text-sm">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="font-medium">{repair.title}</span>
                        <span className={`ml-2 px-2 py-0.5 rounded text-xs font-medium ${badge.color}`}>{badge.label}</span>
                      </div>
                      <span className="text-gray-500 text-xs">{formatDate(repair.created_at)}</span>
                    </div>
                    {repair.description && <p className="mt-1 text-gray-600 text-xs">{repair.description}</p>}
                    <div className="mt-2 flex gap-3 text-xs text-gray-500">
                      {repair.estimated_cost && <span>Оценка: {formatMoney(repair.estimated_cost)}</span>}
                      {repair.actual_cost && <span>Факт: {formatMoney(repair.actual_cost)}</span>}
                      {repair.assigned_to_name && <span>Исполнитель: {repair.assigned_to_name}</span>}
                      {repair.actual_completion_date && <span>Завершено: {formatDate(repair.actual_completion_date)}</span>}
                    </div>
                    {repair.completion_notes && (
                      <p className="mt-1 text-xs text-gray-500 italic">{repair.completion_notes}</p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
</div>
      )}

      {/* Documents */}
      <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-6">
        <AssetDocuments assetId={asset.id} assetName={asset.name} />
      </div>

      {/* Photo Gallery Modal */}
      <AssetPhotoGallery
        assetId={asset.id}
        assetName={asset.name}
        isOpen={isGalleryOpen}
        onClose={() => setIsGalleryOpen(false)}
      />
    </div>
  );
};

export default AssetDetailsModal;
