// frontend/src/components/assets/AddAssetForm.tsx
import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import type { Asset, AssetTypeConfig } from '../../types';

interface AddAssetFormProps {
  onSubmit: (data: Omit<Asset, 'id' | 'created_at' | 'updated_at'>) => Promise<void>;
  onClose: () => void;
}

const AddAssetForm: React.FC<AddAssetFormProps> = ({ onSubmit, onClose }) => {
  const [assetTypes, setAssetTypes] = useState<AssetTypeConfig[]>([]);
  const [selectedType, setSelectedType] = useState<string>('');
  const [deptTree, setDeptTree] = useState<any[]>([]);
  const [employees, setEmployees] = useState<any[]>([]);
  const [selectedRoomId, setSelectedRoomId] = useState<number | ''>('');
  const [selectedResponsibleId, setSelectedResponsibleId] = useState<number | ''>('');
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | ''>('');
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [responsibleOptions, setResponsibleOptions] = useState<any[]>([]);
  const [storageAddresses, setStorageAddresses] = useState<any[]>([]);
  const [selectedStorageAddressId, setSelectedStorageAddressId] = useState<number | ''>('');
  const [storageSearchQuery, setStorageSearchQuery] = useState('');
  const [storageDropdownOpen, setStorageDropdownOpen] = useState(false);

  // Закрытие dropdown при клике вне
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('.storage-search-container')) {
        setStorageDropdownOpen(false);
      }
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  // Загрузка складских полок
  useEffect(() => {
    const token = localStorage.getItem('token');
    fetch('/api/storage-addresses/rooms/all?room_type=warehouse', {
      headers: { 'Authorization': `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : [])
      .catch(() => [])
      .then(rooms => {
        if (!Array.isArray(rooms) || rooms.length === 0) return;
        
        const loadTrees = Promise.all(
          rooms.map((room: any) =>
            fetch(`/api/storage-addresses/rooms/${room.id}/tree`, {
              headers: { 'Authorization': `Bearer ${token}` },
            })
              .then(r => r.ok ? r.json() : { zones: [], storage_tree: [] })
              .catch(() => ({ zones: [], storage_tree: [] }))
          )
        );
        
        loadTrees.then(trees => {
          const shelves: any[] = [];
          trees.forEach(tree => {
            const collectShelves = (nodes: any[], path: string = '') => {
              for (const node of nodes) {
                const currentPath = path ? `${path} → ${node.name}` : node.name;
                if (node.level === 'shelf') {
                  shelves.push({
                    id: node.id,
                    name: node.name,
                    full_address: currentPath,
                  });
                }
                if (node.children) {
                  collectShelves(node.children, currentPath);
                }
              }
            };
            collectShelves(tree.zones || []);
            collectShelves(tree.storage_tree || []);
          });
          setStorageAddresses(shelves);
        });
      });
  }, []);

  const filteredShelves = storageAddresses.filter(sa =>
    sa.full_address.toLowerCase().includes(storageSearchQuery.toLowerCase()) ||
    sa.name.toLowerCase().includes(storageSearchQuery.toLowerCase())
  );

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<any>({
    defaultValues: {
      status: 'active',
    },
  });

  const watchAssetType = watch('asset_type');

  useEffect(() => {
    fetch('/api/asset-types')
      .then(r => r.json())
      .then(setAssetTypes)
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (watchAssetType && assetTypes.length > 0) {
      const typeConfig = assetTypes.find(t => t.code === watchAssetType);
      if (typeConfig) {
        setSelectedType(typeConfig.code);
        if (typeConfig.default_depreciation_years && !watch('depreciation_years')) {
          setValue('depreciation_years', typeConfig.default_depreciation_years);
        }
      }
    }
  }, [watchAssetType, assetTypes]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    Promise.all([
    fetch('/api/admin/placements/tree', { headers: { 'Authorization': `Bearer ${token}` } }).then(r => r.json()).catch(() => []),
    fetch('/api/admin/placement-assignments/employees', { headers: { 'Authorization': `Bearer ${token}` } }).then(r => r.json()).catch(() => []),
    fetch('/api/admin/placement-assignments/responsible-persons', { headers: { 'Authorization': `Bearer ${token}` } }).then(r => r.json()).catch(() => []),
    fetch('/api/storage-addresses', { headers: { 'Authorization': `Bearer ${token}` } }).then(r => r.json()).catch(() => []),
    ]).then(([tree, emps, responsibleUsers, storageAddrs]) => {
      const safeTree = Array.isArray(tree) ? tree : [];
      const safeEmps = Array.isArray(emps) ? emps : [];
      const safeResponsibleUsers = Array.isArray(responsibleUsers) ? responsibleUsers : [];
      const safeStorageAddrs = Array.isArray(storageAddrs) ? storageAddrs : [];
      setDeptTree(safeTree);
      setEmployees(safeEmps);
      const empList = safeEmps.map((emp: any) => ({
        id: emp.id,
        name: emp.full_name || `${emp.last_name} ${emp.first_name}`,
        departmentName: emp.department_name || emp.department_code || '',
        fullName: `${emp.full_name || emp.last_name} ${emp.first_name}${emp.department_name ? ` (${emp.department_name})` : ''}`,
      }));
      setResponsibleOptions(safeResponsibleUsers.map((u: any) => ({
        id: u.id,
        name: u.name,
        fullName: u.full_name,
      })));
      setStorageAddresses(safeStorageAddrs);
      setLoadingOptions(false);
    });
  }, []);

  const getAllRooms = () => {
    const rooms: Array<{ id: number; deptId: number; deptName: string; deptCode: string; roomId: number; roomName: string; fullName: string }> = [];
    deptTree.forEach(dept => {
      dept.rooms?.forEach((room: { id: number; name: string; floor?: string; building?: string }) => {
        let loc = room.name;
        if (room.floor) loc += ` - ${room.floor}`;
        if (room.building) loc += ` (${room.building})`;
        rooms.push({
          id: dept.id,
          deptId: dept.id,
          deptName: dept.name,
          deptCode: dept.code,
          roomId: room.id,
          roomName: room.name,
          fullName: `${dept.name} - ${loc}`,
        });
      });
    });
    return rooms;
  };

  const getAllEmployees = () => {
    return employees.map(emp => ({
      id: emp.id,
      name: emp.full_name || `${emp.last_name} ${emp.first_name}`,
      departmentName: emp.department_name || emp.department_code || '',
      fullName: `${emp.full_name || emp.last_name} ${emp.first_name}${emp.department_name ? ` (${emp.department_name})` : ''}`,
    }));
  };

  const allRooms = getAllRooms();
  const allEmployees = getAllEmployees();

  const handleSubmitForm = async (data: any) => {
    try {
      await onSubmit({
        inventory_number: data.inventory_number,
        name: data.name,
        description: data.description,
        model: data.model,
        manufacturer_code: data.manufacturer_code,
        manufacturer_name: data.manufacturer_name,
        asset_type: data.asset_type,
        purchase_price: data.purchase_price ? Number(data.purchase_price) : undefined,
        current_value: data.current_value ? Number(data.current_value) : undefined,
        quantity: data.quantity ? Number(data.quantity) : 1,
        status: data.status as Asset['status'],
        location_address: data.location_address,
        responsible_person: data.responsible_person,
        department_code: data.department_code,
        employee_id: selectedEmployeeId || undefined,
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
        rfid_tag: data.rfid_tag,
        storage_address_id: selectedStorageAddressId || undefined,
        is_active: true,
      });
      reset();
      setSelectedType('');
    } catch (error) {
      console.error('Ошибка отправки формы:', error);
    }
  };

  if (loadingOptions) {
    return (
      <div className="flex justify-center py-8">
        <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <span className="ml-3 text-gray-600 dark:text-gray-300">Загрузка данных...</span>
      </div>
    );
  }

  return (
    <>
      <form onSubmit={handleSubmit(handleSubmitForm)} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
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
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="INV-001"
            />
            {errors.inventory_number && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{String(errors.inventory_number.message)}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
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
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Название актива"
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{String(errors.name.message)}</p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
              Тип актива
            </label>
            <select
              {...register('asset_type')}
              onChange={(e) => {
                const selectedCode = e.target.value;
                const typeConfig = assetTypes.find(t => t.code === selectedCode);
                if (typeConfig && typeConfig.default_depreciation_years) {
                  setValue('depreciation_years', typeConfig.default_depreciation_years);
                }
              }}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
              Срок амортизации (лет)
            </label>
            <input
              type="number"
              min="1"
              {...register('depreciation_years', {
                valueAsNumber: true,
              })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="5"
            />
          </div>
        </div>

        {selectedType === 'fire_extinguisher' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Объём (л)
              </label>
              <input
                type="number"
                step="0.1"
                {...register('capacity', { valueAsNumber: true })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Следующая проверка
              </label>
              <input
                type="date"
                {...register('next_maintenance_date')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        )}

        {(selectedType === 'computer' || selectedType === 'printer') && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Серийный номер
              </label>
              <input
                type="text"
                {...register('serial_number')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="SN-12345"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Мощность (Вт)
              </label>
              <input
                type="text"
                {...register('power')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="300"
              />
            </div>
          </div>
        )}

        {selectedType === 'printer' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Тип тонера
              </label>
              <input
                type="text"
                {...register('consumable_type')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="CF280A"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Следующее обслуживание
              </label>
              <input
                type="date"
                {...register('next_maintenance_date')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        )}

        {selectedType === 'crypto_token' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Имя пользователя / Логин
              </label>
              <input
                type="text"
                {...register('crypto_wallet_address')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="ivanov.a"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Серийный номер / Идентификатор
              </label>
              <input
                type="text"
                {...register('crypto_token_symbol')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="SN-XXXXX"
              />
            </div>
          </div>
        )}

        {selectedType === 'consumables' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Тип расходника
              </label>
              <input
                type="text"
                {...register('consumable_type')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Бумага А4"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Вес (кг)
              </label>
              <input
                type="text"
                {...register('weight')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="1.5"
              />
            </div>
          </div>
        )}

        {(selectedType === 'ventilation' || selectedType === 'electrical' || selectedType === 'plumbing') && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Мощность (Вт)
              </label>
              <input
                type="text"
                {...register('power')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="1500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Следующая проверка
              </label>
              <input
                type="date"
                {...register('next_maintenance_date')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        )}

        {(selectedType === 'it_network' || selectedType === 'multifunction' || selectedType === 'communication') && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Серийный номер
              </label>
              <input
                type="text"
                {...register('serial_number')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="SN-12345"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                MAC-адрес / IP
              </label>
              <input
                type="text"
                {...register('model')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="00:1A:2B:3C:4D:5E"
              />
            </div>
          </div>
        )}

        {selectedType === 'power_supply' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Мощность (Вт/кВА)
              </label>
              <input
                type="text"
                {...register('power')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="1000"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Время автономной работы (мин)
              </label>
              <input
                type="number"
                {...register('capacity')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="30"
              />
            </div>
          </div>
        )}

        {selectedType === 'security' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Серийный номер
              </label>
              <input
                type="text"
                {...register('serial_number')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="SN-12345"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Следующая проверка
              </label>
              <input
                type="date"
                {...register('next_maintenance_date')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        )}

        {selectedType === 'tools' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Серийный номер
              </label>
              <input
                type="text"
                {...register('serial_number')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="SN-12345"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Вес (кг)
              </label>
              <input
                type="text"
                {...register('weight')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="2.5"
              />
            </div>
          </div>
        )}

        {selectedType === 'appliances' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Мощность (Вт)
              </label>
              <input
                type="text"
                {...register('power')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="1000"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Серийный номер
              </label>
              <input
                type="text"
                {...register('serial_number')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="SN-12345"
              />
            </div>
          </div>
        )}

        {(selectedType === 'furniture_server' || selectedType === 'furniture_storage') && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Высота (RU)
              </label>
              <input
                type="number"
                {...register('capacity')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="42"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Вес (кг)
              </label>
              <input
                type="text"
                {...register('weight')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="150"
              />
            </div>
          </div>
        )}

        {selectedType === 'parking' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Емкость / Количество мест
              </label>
              <input
                type="number"
                {...register('capacity')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Площадь (м²)
              </label>
              <input
                type="text"
                {...register('weight')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="500"
              />
            </div>
          </div>
        )}

        {selectedType === 'doors_windows' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Количество (шт)
              </label>
              <input
                type="number"
                {...register('capacity')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Материал / Тип
              </label>
              <input
                type="text"
                {...register('model')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Пластик, дерево, металл"
              />
            </div>
          </div>
        )}

        {selectedType === 'ppe' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Размер
              </label>
              <input
                type="text"
                {...register('model')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="M, L, XL"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                Срок замены
              </label>
              <input
                type="date"
                {...register('warranty_expiry')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
              Дата покупки
            </label>
            <input
              type="date"
              {...register('purchase_date')}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
              Гарантия до
            </label>
            <input
              type="date"
              {...register('warranty_expiry')}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
              Модель
            </label>
            <input
              type="text"
              {...register('model')}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Модель"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
              Код производителя
            </label>
            <input
              type="text"
              {...register('manufacturer_code')}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Код производителя"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
            Производитель
          </label>
          <input
            type="text"
            {...register('manufacturer_name')}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Производитель"
          />
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
              Стоимость покупки (₽)
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              {...register('purchase_price', {
                valueAsNumber: true,
              })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="0.00"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
              Текущая стоимость (₽)
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              {...register('current_value', {
                valueAsNumber: true,
              })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="0.00"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
              Количество
            </label>
            <input
              type="number"
              min="1"
              {...register('quantity', {
                valueAsNumber: true,
                value: 1,
              })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="1"
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
              Подразделение / Кабинет
            </label>
            <select
              value={selectedRoomId}
              onChange={(e) => {
                const roomId = e.target.value ? Number(e.target.value) : null;
                setSelectedRoomId(roomId || '');
                if (roomId) {
                  const room = allRooms.find(r => r.roomId === roomId);
                  if (room) {
                    setValue('department_code', room.deptCode);
                    setValue('location_address', room.fullName);
                  }
                } else {
                  setValue('department_code', '');
                  setValue('location_address', '');
                }
              }}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loadingOptions || allRooms.length === 0}
            >
              <option value="">Не выбрано</option>
              {allRooms.map(room => (
                <option key={room.roomId} value={room.roomId}>
                  {room.fullName}
                </option>
              ))}
            </select>
            {allRooms.length === 0 && !loadingOptions && (
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Нет доступных кабинетов</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
              Ответственное лицо
            </label>
            <select
              value={selectedResponsibleId}
              onChange={(e) => {
                const empId = e.target.value ? Number(e.target.value) : null;
                setSelectedResponsibleId(empId || '');
                if (empId) {
                  const emp = responsibleOptions.find((emp: any) => emp.id === empId);
                  if (emp) {
                    setValue('responsible_person', emp.name);
                  }
                } else {
                  setValue('responsible_person', '');
                }
              }}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loadingOptions || responsibleOptions.length === 0}
            >
              <option value="">Не выбрано</option>
              {responsibleOptions.map(emp => (
                <option key={emp.id} value={emp.id}>
                  {emp.fullName}
                </option>
              ))}
            </select>
            {responsibleOptions.length === 0 && !loadingOptions && (
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Нет доступных сотрудников</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
              Сотрудник (получатель имущества)
            </label>
            <select
              value={selectedEmployeeId}
              onChange={(e) => {
                const empId = e.target.value ? Number(e.target.value) : null;
                setSelectedEmployeeId(empId || '');
              }}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loadingOptions || allEmployees.length === 0}
            >
              <option value="">Не выбран</option>
              {allEmployees.map(emp => (
                <option key={emp.id} value={emp.id}>
                  {emp.fullName}
                </option>
              ))}
            </select>
            {allEmployees.length === 0 && !loadingOptions && (
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Нет доступных сотрудников</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
              Статус
            </label>
            <select
              {...register('status', { required: 'Обязательное поле' })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="active">Активен</option>
              <option value="maintenance">На ремонте</option>
              <option value="reserved">В резерве</option>
              <option value="decommissioned">Выведен</option>
              <option value="lost">Утерян</option>
              <option value="written_off">Списан</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
            Описание
          </label>
          <textarea
            {...register('description')}
            rows={3}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Описание актива..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
            📡 RFID-метка
          </label>
          <input
            type="text"
            {...register('rfid_tag')}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Уникальный ID RFID-метки (для сканера)"
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Если заполнено, RFID-сканер сможет находить этот актив по метке
          </p>
        </div>

        <div className="storage-search-container">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
            📍 Адрес хранения (склад → стеллаж → полка)
          </label>
          <div className="relative">
            <input
              type="text"
              value={storageSearchQuery}
              onChange={(e) => {
                setStorageSearchQuery(e.target.value);
                setStorageDropdownOpen(true);
              }}
              onFocus={() => setStorageDropdownOpen(true)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Поиск склада, стеллажа, полки..."
            />
            {storageDropdownOpen && filteredShelves.length > 0 && (
              <div className="absolute z-50 mt-1 w-full max-h-60 overflow-y-auto bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg">
                {filteredShelves.map((sa: any) => (
                  <div
                    key={sa.id}
                    onClick={() => {
                      setSelectedStorageAddressId(sa.id);
                      setValue('storage_address_id', sa.id);
                      setValue('storage_address_name', sa.full_address);
                      setStorageSearchQuery(sa.full_address);
                      setStorageDropdownOpen(false);
                    }}
                    className="px-4 py-2.5 hover:bg-blue-50 dark:hover:bg-blue-900/20 cursor-pointer text-sm text-gray-900 dark:text-gray-100 border-b border-gray-100 dark:border-gray-700 last:border-b-0"
                  >
                    <div className="font-medium">{sa.full_address}</div>
                  </div>
                ))}
              </div>
            )}
            {storageDropdownOpen && filteredShelves.length === 0 && storageSearchQuery && (
              <div className="absolute z-50 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                Ничего не найдено
              </div>
            )}
          </div>
          {storageAddresses.length === 0 && !loadingOptions && (
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Нет доступных ячеек склада</p>
          )}
        </div>

        <div className="flex gap-3 pt-4">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition text-gray-700 dark:text-gray-200"
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
              'Добавить'
            )}
          </button>
        </div>
      </form>
    </>
  );
};

export default AddAssetForm;
