// frontend/src/components/assets/AssetDetailsModal.tsx
import React, { useState, useEffect, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { Calendar, DollarSign, Edit, Trash2, MapPin, User, Wrench, Plus, RefreshCw, Image, ClipboardCheck, CheckCircle2, Clock, Printer, Radio } from 'lucide-react';
import type { Asset, MaintenanceEvent } from '../../types';
import { AssetStatusMap, MaintenanceEventTypes, AssetTypeNames } from '../../types';
import { formatMoney, formatDate } from '../../utils/helpers';
import toast from 'react-hot-toast';
import AssetPhotoGallery from './AssetPhotoGallery';
import AssetDocuments from './AssetDocuments';
import { useAssetPhotos } from '../../hooks/useAssetPhotos';
import api from '../../api/client';

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
  const [printPhotos, setPrintPhotos] = useState<string[]>([]);
  const [printPhotosMeta, setPrintPhotosMeta] = useState<any[]>([]);
  const [isPreparingPrint, setIsPreparingPrint] = useState(false);
  const { photos: assetPhotos } = useAssetPhotos(asset?.id ?? 0);
  
  // Состояния для подготовки фотографий к печати
  const [printPhotosFull, setPrintPhotosFull] = useState<{ src: string; meta: any }[]>([]);
  const [isPreparingPrintFull, setIsPreparingPrintFull] = useState(false);
  const [shouldPrint, setShouldPrint] = useState(false);
  
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
      const res = await api.get(`/maintenance-events/asset/${asset.id}`);
      setMaintenanceEvents(res.data.items || []);
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
      const res = await api.get(`/assets/${asset.id}/repair-history`);
      setRepairHistory(res.data.items || []);
    } catch (err) {
      console.error('Ошибка загрузки истории ремонтов:', err);
    } finally {
      setLoadingRepairs(false);
    }
  };

  const handlePreparePrint = async () => {
    if (!asset) return;
    setIsPreparingPrint(true);
    try {
      // Собираем фотографии как data URL с метаданными для печати
      const dataUrls: string[] = [];
      const photosMeta: any[] = [];
      let loadErrors = 0;
      
      for (const photo of assetPhotos) {
        try {
          const res = await api.get(`/asset-photos/${photo.id}/download`, { 
            responseType: 'blob',
            headers: localStorage.getItem('token') 
              ? { Authorization: `Bearer ${localStorage.getItem('token')}` } 
              : {}
          });
          const dataUrl: string = await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result as string);
            reader.onerror = reject;
            reader.readAsDataURL(res.data as Blob);
          });
          dataUrls.push(dataUrl);
          photosMeta.push({
            category: photo.photo_category,
            description: photo.description,
            stage: photo.stage,
          });
        } catch (err) {
          loadErrors++;
          console.error(`Не удалось загрузить фото ${photo.id} для печати:`, err);
        }
      }
      
      if (loadErrors > 0 && dataUrls.length === 0) {
        toast.error(`Не удалось загрузить фотографии для печати (${loadErrors} ошибок)`);
      } else if (loadErrors > 0) {
        toast.success(`Фотографии подготовлены (${loadErrors} фото не удалось загрузить)`);
      }
      
      setPrintPhotos(dataUrls);
      setPrintPhotosMeta(photosMeta);
      
      // Ждём рендер печатного блока и загрузку изображений
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Дополнительная защита: ждём пока все img элементы загрузятся
      const printSection = document.querySelector('.print-area');
      if (printSection) {
        const images = printSection.querySelectorAll('img');
        let allLoaded = true;
        images.forEach((img) => {
          if (!(img as HTMLImageElement).complete || (img as HTMLImageElement).naturalHeight === 0) {
            allLoaded = false;
          }
        });
        
        if (!allLoaded) {
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      }
      
      window.print();
    } finally {
      setIsPreparingPrint(false);
    }
  };

  const handleAddEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!asset) return;
    try {
      const res = await api.post(`/maintenance-events/asset/${asset.id}`, {
        ...newEvent,
        cost: newEvent.cost ? parseFloat(newEvent.cost) : undefined,
      });
      if (res.status === 200 || res.status === 201 || res.status === 204) {
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
      green: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
      yellow: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
      blue: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
      gray: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
      red: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
      orange: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
    };
    return colors[status] || 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
  };

  const getRepairStatusBadge = (status: string): { label: string; color: string } => {
    const map: Record<string, { label: string; color: string }> = {
      approved: { label: 'Одобрено', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' },
      in_progress: { label: 'В работе', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300' },
      completed: { label: 'Завершено', color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' },
    };
    return map[status] || { label: status, color: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300' };
  };

  const getAssetTypeColor = (color: string): string => {
    const colors: Record<string, string> = {
      amber: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
      red: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
      orange: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
      blue: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
      gray: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
      green: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
    };
    return colors[color] || 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
  };

  const DetailRow = ({ label, value, icon: Icon }: { label: string; value?: string | number; icon?: any }) => (
    <div className="flex items-start space-x-3 py-3 border-b border-gray-100 dark:border-gray-700 last:border-0">
      {Icon && <Icon className="w-5 h-5 text-gray-400 dark:text-gray-500 mt-0.5" />}
      <div>
        <p className="text-xs text-gray-500 dark:text-gray-400 uppercase">{label}</p>
        <p className="text-sm text-gray-800 dark:text-gray-100 mt-0.5">{value || <span className="text-gray-400 dark:text-gray-500 italic">Не указано</span>}</p>
      </div>
    </div>
  );

  // Карта специфичных полей для типов активов
  const assetTypeFieldMap: Record<string, string[]> = {
    // Офисное оборудование
    'computer': ['serial_number', 'manufacturer_name', 'manufacturer_code', 'model', 'capacity', 'power', 'weight'],
    'printer': ['serial_number', 'manufacturer_name', 'manufacturer_code', 'model', 'consumable_type'],
    'multifunction': ['serial_number', 'manufacturer_name', 'manufacturer_code', 'model', 'consumable_type'],
    'communication': ['serial_number', 'manufacturer_name', 'manufacturer_code', 'model'],
    'it_network': ['serial_number', 'manufacturer_name', 'manufacturer_code', 'model'],
    'furniture_server': ['serial_number', 'manufacturer_name', 'manufacturer_code', 'model', 'weight'],
    
    // Мебель
    'furniture': ['serial_number', 'manufacturer_name', 'manufacturer_code', 'model', 'weight'],
    'furniture_server': ['serial_number', 'manufacturer_name', 'manufacturer_code', 'model', 'weight'],
    'furniture_storage': ['serial_number', 'manufacturer_name', 'manufacturer_code', 'model', 'weight'],
    
    // Инженерные системы
    'ventilation': ['serial_number', 'manufacturer_name', 'manufacturer_code', 'model', 'power', 'capacity', 'weight'],
    'electrical': ['serial_number', 'manufacturer_name', 'manufacturer_code', 'model', 'power', 'weight'],
    'power_supply': ['serial_number', 'manufacturer_name', 'manufacturer_code', 'model', 'power', 'capacity', 'weight'],
    'security': ['serial_number', 'manufacturer_name', 'manufacturer_code', 'model', 'power'],
    'plumbing': ['serial_number', 'manufacturer_name', 'manufacturer_code', 'model', 'capacity'],
    'doors_windows': ['serial_number', 'manufacturer_name', 'manufacturer_code', 'model'],
    'parking': ['serial_number', 'manufacturer_name', 'manufacturer_code', 'model'],
    
    // Прочее
    'fire_extinguisher': ['serial_number', 'manufacturer_name', 'manufacturer_code', 'model', 'capacity', 'weight'],
    'crypto_token': ['crypto_wallet_address', 'crypto_token_symbol'],
    'consumables': ['consumable_type'],
    'tools': ['serial_number', 'manufacturer_name', 'manufacturer_code', 'model', 'weight'],
    'appliances': ['serial_number', 'manufacturer_name', 'manufacturer_code', 'model', 'power', 'capacity', 'weight'],
    'ppe': [], // СИЗ — только базовые поля
    'other': [], // Прочее — только базовые поля
  };

  // Получаем разрешённые поля для текущего типа актива
  const assetTypeCode = asset.asset_type || '';
  const allowedFields = assetTypeCode ? (assetTypeFieldMap[assetTypeCode] || []) : [];

  // Проверяем, разрешено ли поле для данного типа
  const isFieldAllowed = (fieldName: string): boolean => {
    // Базовые поля всегда показываем
    const baseFields = ['inventory_number', 'name', 'description', 'model', 'manufacturer_name', 'manufacturer_code', 'serial_number', 'rfid_tag', 'quantity', 'depreciation_years'];
    if (baseFields.includes(fieldName)) return true;
    // Если для типа заданы поля — показываем только их
    if (allowedFields.length > 0) return allowedFields.includes(fieldName);
    // Иначе показываем только если есть значение
    return true;
  };

  // Собираем данные для печати в структуру
  const printSections: { title: string; content: React.ReactNode }[] = useMemo(() => {
    // Вспомогательные функции внутри useMemo для правильного замыкания
    const printRow = (label: string, value?: string | number | null | undefined) => {
      if (value === undefined || value === null || value === '') return null;
      if (typeof value === 'string' && value.trim() === '') return null;
      if (typeof value === 'number' && isNaN(value)) return null;
      return (
        <div style={{ display: 'flex', padding: '3px 0', fontSize: '11px', pageBreakInside: 'avoid' }}>
          <span style={{ width: '180px', fontWeight: 'bold', color: '#000', flexShrink: 0 }}>{label}</span>
          <span style={{ color: '#333' }}>{value}</span>
        </div>
      );
    };
    
    const printSection = (title: string, rows: React.ReactNode[]) => {
      const validRows = rows.filter(r => r !== null && r !== undefined);
      if (validRows.length === 0) return null;
      return (
        <div className="print-section" style={{ marginBottom: '16px' }}>
          <h2 style={{ fontSize: '13px', fontWeight: 'bold', borderBottom: '1px solid #000', paddingBottom: '3px', margin: '0 0 8px', textTransform: 'uppercase' }}>{title}</h2>
          {validRows}
        </div>
      );
    };
    
    const getCategoryLabel = (category: string): string => {
      const labels: Record<string, string> = {
        general_view: '📷 Общий вид',
        placement: '📍 Место размещения',
        inventory_number: '🔢 Инвентарный номер',
        current_location: '🗺️ Текущее местоположение',
        condition: '🔍 Состояние',
        malfunction: '⚠️ Неисправность',
        general_condition: '📋 Общее состояние',
      };
      return labels[category] || category;
    };
    
    const sections: { title: string; content: React.ReactNode }[] = [];
    
    // Основная информация
    const mainInfoRows: React.ReactNode[] = [
      printRow('Инвентарный номер', asset.inventory_number),
      printRow('Название', asset.name),
      printRow('Описание', asset.description),
      printRow('Модель', asset.model),
      printRow('Тип актива', assetTypeInfo ? `${assetTypeInfo.icon} ${assetTypeInfo.label}` : asset.asset_type),
      printRow('Статус', statusInfo?.label || asset.status),
      printRow('Производитель', asset.manufacturer_name),
      printRow('Код производителя', asset.manufacturer_code),
      printRow('Серийный номер', asset.serial_number),
      printRow('RFID-метка', asset.rfid_tag),
      ...(asset.quantity && asset.quantity > 1 ? [printRow('Количество', asset.quantity)] : []),
      ...(asset.depreciation_years != null ? [printRow('Срок амортизации', `${asset.depreciation_years} лет`)] : []),
      ...(isFieldAllowed('capacity') && asset.capacity ? [printRow('Объём', `${asset.capacity} л`)] : []),
      ...(isFieldAllowed('power') && asset.power ? [printRow('Мощность', `${asset.power} Вт`)] : []),
      ...(isFieldAllowed('weight') && asset.weight ? [printRow('Вес', `${asset.weight}`)] : []),
      ...(isFieldAllowed('consumable_type') && asset.consumable_type ? [printRow('Тип расходника', asset.consumable_type)] : []),
      ...(isFieldAllowed('crypto_wallet_address') && asset.crypto_wallet_address ? [printRow('Имя пользователя / Логин', asset.crypto_wallet_address)] : []),
      ...(isFieldAllowed('crypto_token_symbol') && asset.crypto_token_symbol ? [printRow('Серийный номер / Идентификатор', asset.crypto_token_symbol)] : []),
    ];
    if (mainInfoRows.some(r => r != null)) {
      sections.push({ title: 'Основная информация', content: printSection('Основная информация', mainInfoRows) });
    }
    
    // Финансы
    const financeRows: React.ReactNode[] = [
      printRow('Стоимость покупки', asset.purchase_price != null ? formatMoney(asset.purchase_price) : undefined),
      printRow('Текущая стоимость', asset.current_value != null ? formatMoney(asset.current_value) : undefined),
    ];
    if (financeRows.some(r => r != null)) {
      sections.push({ title: 'Финансы', content: printSection('Финансовые данные', financeRows) });
    }
    
    // Даты
    const dateRows: React.ReactNode[] = [
      printRow('Создан', formatDate(asset.created_at)),
      printRow('Обновлён', formatDate(asset.updated_at)),
      printRow('Дата покупки', asset.purchase_date ? formatDate(asset.purchase_date) : undefined),
      printRow('Дата ввода в эксплуатацию', asset.commissioning_date ? formatDate(asset.commissioning_date) : undefined),
      printRow('Гарантия до', asset.warranty_expiry ? formatDate(asset.warranty_expiry) : undefined),
      printRow('Следующее обслуживание', asset.next_maintenance_date ? formatDate(asset.next_maintenance_date) : undefined),
    ];
    if (dateRows.some(r => r != null)) {
      sections.push({ title: 'Даты', content: printSection('Даты', dateRows) });
    }
    
    // Местоположение
    const locationRows: React.ReactNode[] = [
      printRow('Адрес', asset.location_address),
      printRow('Подразделение', asset.department_name || asset.department_code),
      printRow('Ответственное лицо', asset.responsible_person || asset.employee_name),
    ];
    if (locationRows.some(r => r != null)) {
      sections.push({ title: 'Местоположение', content: printSection('Местоположение и ответственность', locationRows) });
    }
    
    // История обслуживания
    if (maintenanceEvents.length > 0) {
      sections.push({
        title: 'История обслуживания',
        content: (
          <div className="print-section" style={{ marginBottom: '16px' }}>
            <h2 style={{ fontSize: '13px', fontWeight: 'bold', borderBottom: '1px solid #000', paddingBottom: '3px', margin: '0 0 8px', textTransform: 'uppercase' }}>История обслуживания (последние 10)</h2>
            <table className="print-table">
              <thead>
                <tr>
                  <th style={{ width: '80px' }}>Дата</th>
                  <th style={{ width: '120px' }}>Тип</th>
                  <th>Описание</th>
                  <th style={{ width: '80px' }}>Стоимость</th>
                  <th style={{ width: '120px' }}>Выполнил</th>
                </tr>
              </thead>
              <tbody>
                {maintenanceEvents.slice(0, 10).map((event) => {
                  const eventTypeInfo = MaintenanceEventTypes[event.event_type as keyof typeof MaintenanceEventTypes];
                  return (
                    <tr key={event.id}>
                      <td>{formatDate(event.event_date)}</td>
                      <td>{eventTypeInfo?.icon || '🔧'} {eventTypeInfo?.label || event.event_type}</td>
                      <td>{event.description || '—'}</td>
                      <td>{event.cost ? formatMoney(event.cost) : '—'}</td>
                      <td>{event.performed_by || '—'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )
      });
    }
    
    // Заявки на ремонт
    if (repairHistory.length > 0) {
      sections.push({
        title: 'Заявки на ремонт',
        content: (
          <div className="print-section" style={{ marginBottom: '16px' }}>
            <h2 style={{ fontSize: '13px', fontWeight: 'bold', borderBottom: '1px solid #000', paddingBottom: '3px', margin: '0 0 8px', textTransform: 'uppercase' }}>Заявки на ремонт</h2>
            <table className="print-table">
              <thead>
                <tr>
                  <th style={{ width: '80px' }}>Дата</th>
                  <th>Название</th>
                  <th style={{ width: '80px' }}>Статус</th>
                  <th style={{ width: '80px' }}>Оценка</th>
                  <th style={{ width: '80px' }}>Факт</th>
                  <th style={{ width: '100px' }}>Исполнитель</th>
                </tr>
              </thead>
              <tbody>
                {repairHistory.map((repair: any) => {
                  const badge = getRepairStatusBadge(repair.status);
                  return (
                    <tr key={repair.id}>
                      <td>{formatDate(repair.created_at)}</td>
                      <td>{repair.title}</td>
                      <td>{badge.label}</td>
                      <td>{repair.estimated_cost ? formatMoney(repair.estimated_cost) : '—'}</td>
                      <td>{repair.actual_cost ? formatMoney(repair.actual_cost) : '—'}</td>
                      <td>{repair.assigned_to_name || '—'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )
      });
    }
    
    // Проверка наличия
    const inventoryRows: React.ReactNode[] = [];
    if (asset.last_inventory_confirmed || asset.last_inventory_date) {
      inventoryRows.push(printRow('Статус', asset.last_inventory_confirmed ? 'Подтверждён' : 'Ожидает'));
    }
    if (asset.last_inventory_date) {
      inventoryRows.push(printRow('Дата проверки', formatDate(asset.last_inventory_date)));
    }
    if (asset.last_inventory_by_id != null) {
      inventoryRows.push(printRow('Проверял (ID)', String(asset.last_inventory_by_id)));
    }
    if (asset.last_inventory_source) {
      inventoryRows.push(printRow('Источник', asset.last_inventory_source === 'rfid' ? 'RFID-сканер' : 'Ручная проверка'));
    }
    if (inventoryRows.length > 0) {
      sections.push({ title: 'Проверка', content: printSection('Проверка наличия', inventoryRows) });
    }
    
    // Фотографии
    if (printPhotosFull.length > 0) {
      sections.push({
        title: 'Фотографии',
        content: (
          <div className="print-section" data-has-content="true" style={{ marginBottom: '16px' }}>
            <h2 style={{ fontSize: '13px', fontWeight: 'bold', borderBottom: '1px solid #000', paddingBottom: '3px', margin: '0 0 8px', textTransform: 'uppercase' }}>Фотографии ({printPhotosFull.length})</h2>
            <div className="print-photos">
              {printPhotosFull.map((photo, i) => (
                <div key={i} className="print-photo">
                  <img src={photo.src} alt={`Фото ${i + 1}`} />
                  <div className="photo-caption">
                    {photo.meta.category && (
                      <span className="photo-category">{getCategoryLabel(photo.meta.category)}</span>
                    )}
                    {photo.meta.description && <span>{photo.meta.description}</span>}
                    {photo.meta.taken_at && <span style={{ display: 'block', color: '#999' }}>{formatDate(photo.meta.taken_at)}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
      });
    }
    
    return sections;
  }, [
    asset,
    assetTypeInfo,
    statusInfo,
    maintenanceEvents,
    repairHistory,
    printPhotosFull,
    isFieldAllowed,
    formatMoney,
    formatDate,
    getRepairStatusBadge,
  ]);

  // QR-код для актива
  const assetUrl = `${window.location.origin}/assets/${asset.id}`;
  const qrCodeData = encodeURIComponent(JSON.stringify({ id: asset.id, inventory: asset.inventory_number, url: assetUrl }));
  const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=100x100&data=${qrCodeData}`;

  const handlePreparePrintFull = async () => {
    if (!asset) return;
    setIsPreparingPrintFull(true);
    try {
      const photosData: { src: string; meta: any }[] = [];
      let loadErrors = 0;
      
      for (const photo of assetPhotos) {
        try {
          const res = await api.get(`/asset-photos/${photo.id}/download`, { 
            responseType: 'blob',
          });
          const dataUrl = await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result as string);
            reader.onerror = reject;
            reader.readAsDataURL(res.data as Blob);
          });
          photosData.push({
            src: dataUrl as string,
            meta: {
              category: photo.photo_category,
              description: photo.description,
              stage: photo.stage,
              taken_at: photo.taken_at,
            },
          });
        } catch (err) {
          loadErrors++;
          console.error(`Не удалось загрузить фото ${photo.id} для печати:`, err);
        }
      }
      
      setPrintPhotosFull(photosData);
      setShouldPrint(true);
    } finally {
      setIsPreparingPrintFull(false);
    }
  };

  // Печать после ре-рендера с загруженными фото
  useEffect(() => {
    if (shouldPrint) {
      console.log('🖨️ shouldPrint=true, printSections:', printSections.length);
      // Даем React отрендерить обновленный DOM и изображениям загрузиться
      const timer = setTimeout(() => {
        console.log('🖨️ window.print() triggered');
        window.print();
        setShouldPrint(false);
      }, 800);
      return () => clearTimeout(timer);
    }
  }, [shouldPrint, printSections]);

return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <h3 className="text-2xl font-bold text-gray-800 dark:text-gray-100">{asset.name}</h3>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(statusInfo?.color || 'gray')}`}>
              {statusInfo?.label || asset.status}
            </span>
            {!asset.is_active && (
              <span className="px-3 py-1 rounded-full text-sm font-medium bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300">
                Скрыт
              </span>
            )}
            {assetTypeInfo && (
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getAssetTypeColor(assetTypeInfo.color)}`}>
                {assetTypeInfo.icon} {assetTypeInfo.label}
              </span>
            )}
          </div>
          <p className="text-lg text-gray-600 dark:text-gray-300 font-mono">#{asset.inventory_number}</p>
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
          <button
            onClick={handlePreparePrintFull}
            disabled={isPreparingPrintFull}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 text-white text-sm rounded-lg hover:bg-emerald-700 transition whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Printer className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{isPreparingPrintFull ? 'Подготовка...' : 'Печать карточки'}</span>
            <span className="sm:hidden">🖨️</span>
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

      <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-6 space-y-4">
        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">Информация</h4>
        <DetailRow label="Инвентарный номер" value={asset.inventory_number} />
        <DetailRow label="Название" value={asset.name} />
        <DetailRow label="Описание" value={asset.description} />
        <DetailRow label="Модель" value={asset.model} />
        <DetailRow label="Тип актива" value={assetTypeInfo ? `${assetTypeInfo.icon} ${assetTypeInfo.label}` : asset.asset_type} />
        <DetailRow label="Производитель" value={asset.manufacturer_name} />
        <DetailRow label="Код производителя" value={asset.manufacturer_code} />
        {asset.serial_number && <DetailRow label="Серийный номер" value={asset.serial_number} />}
        {asset.rfid_tag ? (
          <div className="flex items-start space-x-3 py-3 border-b border-gray-100 dark:border-gray-700">
            <Radio className="w-5 h-5 text-blue-500 mt-0.5" />
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400 uppercase">RFID-метка</p>
              <p className="text-sm font-mono font-medium text-blue-700 dark:text-blue-300 mt-0.5">{asset.rfid_tag}</p>
              <p className="text-xs text-green-600 dark:text-green-400 mt-1">✓ Метка присвоена и активна</p>
            </div>
          </div>
        ) : (
          <div className="flex items-start space-x-3 py-3 border-b border-gray-100 dark:border-gray-700">
            <Radio className="w-5 h-5 text-gray-400 mt-0.5" />
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400 uppercase">RFID-метка</p>
              <p className="text-sm text-gray-400 dark:text-gray-500 mt-0.5 italic">Метка не присвоена</p>
            </div>
          </div>
        )}
        {asset.depreciation_years && <DetailRow label="Срок амортизации" value={`${asset.depreciation_years} лет`} />}
        {asset.capacity && <DetailRow label="Объём" value={`${asset.capacity} л`} />}
        {asset.power && <DetailRow label="Мощность" value={`${asset.power} Вт`} />}
        {asset.consumable_type && <DetailRow label="Тип расходника" value={asset.consumable_type} />}
        {asset.crypto_wallet_address && <DetailRow label="Имя пользователя / Логин" value={asset.crypto_wallet_address} />}
        {asset.crypto_token_symbol && <DetailRow label="Серийный номер / Идентификатор" value={asset.crypto_token_symbol} />}
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-6 space-y-4">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide flex items-center gap-2">
            <DollarSign className="w-4 h-4" /> Финансы
          </h4>
          <DetailRow label="Стоимость покупки" value={formatMoney(asset.purchase_price)} />
          <DetailRow label="Текущая стоимость" value={formatMoney(asset.current_value)} />
        </div>

        <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-6 space-y-4">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide flex items-center gap-2">
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
        <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-6 space-y-4">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide flex items-center gap-2">
            <MapPin className="w-4 h-4" /> Местоположение
          </h4>
          <DetailRow label="Адрес" value={asset.location_address} />
          <DetailRow label="Подразделение" value={asset.department_code} />
        </div>

        <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-6 space-y-4">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide flex items-center gap-2">
            <User className="w-4 h-4" /> Ответственность
          </h4>
          <DetailRow label="Ответственное лицо" value={asset.responsible_person} />
        </div>
      </div>

      {/* Блок проверки наличия */}
      <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-6 space-y-4">
        <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide flex items-center gap-2">
          <ClipboardCheck className="w-4 h-4 text-blue-500" /> Проверка наличия
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Статус подтверждения */}
          <div className={`p-3 rounded-lg border ${
            asset.last_inventory_confirmed
              ? 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800'
              : asset.last_inventory_date
              ? 'bg-amber-50 border-amber-200 dark:bg-amber-900/20 dark:border-amber-800'
              : 'bg-gray-50 border-gray-200 dark:bg-gray-700/50 dark:border-gray-600'
          }`}>
            <div className="flex items-center gap-2">
              {asset.last_inventory_confirmed ? (
                <CheckCircle2 className="w-5 h-5 text-green-500" />
              ) : asset.last_inventory_date ? (
                <Clock className="w-5 h-5 text-amber-500" />
              ) : (
                <ClipboardCheck className="w-5 h-5 text-gray-400" />
              )}
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Статус</p>
                <p className={`text-sm font-medium ${
                  asset.last_inventory_confirmed
                    ? 'text-green-700 dark:text-green-300'
                    : asset.last_inventory_date
                    ? 'text-amber-700 dark:text-amber-300'
                    : 'text-gray-500 dark:text-gray-400'
                }`}>
                  {asset.last_inventory_confirmed ? 'Подтверждён' : asset.last_inventory_date ? 'Ожидает' : 'Не проверен'}
                </p>
              </div>
            </div>
          </div>

          {/* Дата проверки */}
          <div className="p-3 rounded-lg border border-gray-200 dark:border-gray-600">
            <div className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Дата проверки</p>
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                  {asset.last_inventory_date ? formatDate(asset.last_inventory_date) : '—'}
                </p>
              </div>
            </div>
          </div>

          {/* Кто проверял */}
          <div className="p-3 rounded-lg border border-gray-200 dark:border-gray-600">
            <div className="flex items-center gap-2">
              <User className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Проверял</p>
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                  {asset.last_inventory_by_id ? `ID: ${asset.last_inventory_by_id}` : '—'}
                </p>
              </div>
            </div>
          </div>

          {/* Источник проверки */}
          {asset.last_inventory_date && (
            <div className="p-3 rounded-lg border border-gray-200 dark:border-gray-600">
              <div className="flex items-center gap-2">
                {asset.last_inventory_source === 'rfid' ? (
                  <Radio className="w-5 h-5 text-blue-500" />
                ) : (
                  <User className="w-5 h-5 text-green-500" />
                )}
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Источник</p>
                  <p className={`text-sm font-medium ${
                    asset.last_inventory_source === 'rfid'
                      ? 'text-blue-700 dark:text-blue-300'
                      : 'text-green-700 dark:text-green-300'
                  }`}>
                    {asset.last_inventory_source === 'rfid' ? 'RFID-сканер' : 'Ручная проверка'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-6 space-y-4">
        <div className="flex justify-between items-center">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide flex items-center gap-2">
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
          <form onSubmit={handleAddEvent} className="space-y-3 bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Тип события</label>
                <select
                  value={newEvent.event_type}
                  onChange={e => setNewEvent({...newEvent, event_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                  {eventTypeOptions.map(([key, val]) => (
                    <option key={key} value={key}>{val.icon} {val.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Дата</label>
                <input
                  type="date"
                  value={newEvent.event_date}
                  onChange={e => setNewEvent({...newEvent, event_date: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Выполнял</label>
                <input
                  type="text"
                  value={newEvent.performed_by}
                  onChange={e => setNewEvent({...newEvent, performed_by: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
                  placeholder="ФИО"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Стоимость (₽)</label>
                <input
                  type="number"
                  step="0.01"
                  value={newEvent.cost}
                  onChange={e => setNewEvent({...newEvent, cost: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
                  placeholder="0.00"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Описание</label>
              <textarea
                value={newEvent.description}
                onChange={e => setNewEvent({...newEvent, description: e.target.value})}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
                placeholder="Описание работ..."
              />
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setShowAddEvent(false)}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
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
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">Загрузка...</p>
        ) : maintenanceEvents.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">Нет записей об обслуживании</p>
        ) : (
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {maintenanceEvents.map((event) => {
              const eventTypeInfo = MaintenanceEventTypes[event.event_type as keyof typeof MaintenanceEventTypes];
              return (
                <div key={event.id} className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700 text-sm">
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-2">
                      <span>{eventTypeInfo?.icon || '🔧'}</span>
                      <span className="font-medium text-gray-900 dark:text-gray-100">{eventTypeInfo?.label || event.event_type}</span>
                    </div>
                    <span className="text-gray-500 dark:text-gray-400">{formatDate(event.event_date)}</span>
                  </div>
                  {event.description && <p className="mt-1 text-gray-600 dark:text-gray-300">{event.description}</p>}
                  <div className="mt-2 flex gap-3 text-xs text-gray-500 dark:text-gray-400">
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
        <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-6 space-y-4">
          <div className="flex justify-between items-center">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide flex items-center gap-2">
              <Wrench className="w-4 h-4" /> История ремонтов (заявки)
            </h4>
          </div>

          {loadingRepairs ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">Загрузка...</p>
          ) : repairHistory.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">Нет заявок на ремонт</p>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {repairHistory.map((repair: any) => {
                const badge = getRepairStatusBadge(repair.status);
                return (
                  <div key={repair.id} className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700 text-sm">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="font-medium text-gray-900 dark:text-gray-100">{repair.title}</span>
                        <span className={`ml-2 px-2 py-0.5 rounded text-xs font-medium ${badge.color}`}>{badge.label}</span>
                      </div>
                      <span className="text-gray-500 dark:text-gray-400 text-xs">{formatDate(repair.created_at)}</span>
                    </div>
                    {repair.description && <p className="mt-1 text-gray-600 dark:text-gray-300 text-xs">{repair.description}</p>}
                    <div className="mt-2 flex gap-3 text-xs text-gray-500 dark:text-gray-400">
                      {repair.estimated_cost && <span>Оценка: {formatMoney(repair.estimated_cost)}</span>}
                      {repair.actual_cost && <span>Факт: {formatMoney(repair.actual_cost)}</span>}
                      {repair.assigned_to_name && <span>Исполнитель: {repair.assigned_to_name}</span>}
                      {repair.actual_completion_date && <span>Завершено: {formatDate(repair.actual_completion_date)}</span>}
                    </div>
                    {repair.completion_notes && (
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 italic">{repair.completion_notes}</p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
</div>
      )}

      {/* Documents */}
      <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-6">
        <AssetDocuments assetId={asset.id} assetName={asset.name} />
      </div>

      {/* Photo Gallery Modal */}
      <AssetPhotoGallery
        assetId={asset.id}
        assetName={asset.name}
        assetTypeCode={asset.asset_type}
        isOpen={isGalleryOpen}
        onClose={() => setIsGalleryOpen(false)}
      />

      {/* Печатная версия — полная карточка актива */}
      {createPortal(
        <div className="print-area" data-has-content={printSections.length > 0 || undefined}>
          {/* Шапка организации */}
          <div className="print-org-header">
            <h1>Карточка актива</h1>
            <p>Формирование: {new Date().toLocaleDateString('ru-RU')} в {new Date().toLocaleTimeString('ru-RU')}</p>
          </div>

          {/* Заголовок карточки с QR */}
          <div className="print-card-header">
            <div className="print-card-title">
              <h2>{asset.name}</h2>
              <div className="inventory-number">Инвентарный № {asset.inventory_number}</div>
              <div style={{ fontSize: '12px', color: '#555', marginTop: '4px' }}>
                {assetTypeInfo && `${assetTypeInfo.icon} ${assetTypeInfo.label}`}
                {' • '}{statusInfo?.label || asset.status}
              </div>
            </div>
            <div style={{ textAlign: 'right', marginLeft: '16px' }}>
              <img src={qrCodeUrl} alt="QR-код" className="qr-code-print" />
              <div style={{ fontSize: '8px', color: '#999', marginTop: '2px' }}>Скан для проверки</div>
            </div>
          </div>

          {/* Рендерим только секции с данными */}
          {printSections.length > 0 && printSections.map((section, idx) => (
            <div key={idx} className="print-section" data-has-content="true" style={{ marginBottom: '16px' }}>
              {section.content}
            </div>
          ))}

          {/* Блок подписей — показываем только если есть данные */}
          {printSections.length > 0 && (
            <>
              <div className="print-signatures">
                <div className="print-signature">
                  <div className="sig-label">Составил</div>
                  <div className="sig-line">_________________ / _________________</div>
                </div>
                <div className="print-signature">
                  <div className="sig-label">Ответственное лицо</div>
                  <div className="sig-line">_________________ / {asset.responsible_person || '_____________'}</div>
                </div>
                <div className="print-signature">
                  <div className="sig-label">Утвердил</div>
                  <div className="sig-line">_________________ / _________________</div>
                </div>
              </div>

              {/* Подвал */}
              <div style={{ marginTop: '24px', paddingTop: '8px', borderTop: '1px solid #ccc', fontSize: '9px', color: '#999', textAlign: 'center' }}>
                Документ сформирован автоматически системой PAPI • {assetUrl}
              </div>
            </>
          )}
        </div>,
        document.body
      )}
    </div>
  );
};

export default AssetDetailsModal;
