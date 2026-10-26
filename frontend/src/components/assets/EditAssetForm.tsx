// frontend/src/components/assets/EditAssetForm.tsx
import React, { useState, useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import type { Asset, AssetTypeConfig } from '../../types';

interface EditAssetFormProps {
  existingAsset: Asset;
  onSubmit: (data: Asset) => Promise<void>;
  onClose: () => void;
}

const EditAssetForm: React.FC<EditAssetFormProps> = ({ existingAsset, onSubmit, onClose }) => {
  const [assetTypes, setAssetTypes] = useState<AssetTypeConfig[]>([]);
  const [selectedType, setSelectedType] = useState<string>(existingAsset.asset_type || '');
  const [deptTree, setDeptTree] = useState<any[]>([]);
  const [employees, setEmployees] = useState<any[]>([]);
  const [selectedRoomId, setSelectedRoomId] = useState<number | ''>('');
  const [selectedResponsibleId, setSelectedResponsibleId] = useState<number | ''>('');
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | ''>('');
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [responsibleOptions, setResponsibleOptions] = useState<any[]>([]);
  const [storageAddresses, setStorageAddresses] = useState<any[]>([]);
  const [selectedStorageAddressId, setSelectedStorageAddressId] = useState<number | ''>('');
  const [locationSearchQuery, setLocationSearchQuery] = useState<string>(
    existingAsset.location_address || existingAsset.storage_address_name || ''
  );
  const [locationDropdownOpen, setLocationDropdownOpen] = useState(false);
  const [selectedLocationType, setSelectedLocationType] = useState<string>(''); // 'room' или 'storage'

  // Закрытие dropdown при клике вне
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('.location-search-container')) {
        setLocationDropdownOpen(false);
      }
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  // Загрузка складских полок
  useEffect(() => {
    const loadStorageAddresses = async () => {
      const token = localStorage.getItem('token');
      if (!token) return;

      try {
        const roomsResp = await fetch('/api/storage-addresses/rooms/all?room_type=warehouse', {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (!roomsResp.ok) return;
        const rooms: any[] = await roomsResp.json();
        if (!Array.isArray(rooms) || rooms.length === 0) return;

        const shelves: any[] = [];
        for (const room of rooms) {
          const roomName = room.name || '';
          const treeResp = await fetch(`/api/storage-addresses/rooms/${room.id}/tree`, {
            headers: { 'Authorization': `Bearer ${token}` },
          });
          if (!treeResp.ok) continue;
          const tree = await treeResp.json();

          const collectNodes = (nodes: any[], path: string = '') => {
            for (const node of nodes) {
              const currentPath = path ? `${roomName} → ${path} → ${node.name}` : `${roomName} → ${node.name}`;
              if (node.level === 'shelf' || node.level === 'rack' || node.level === 'zone') {
                shelves.push({
                  id: node.id,
                  name: node.name,
                  full_address: currentPath,
                  level: node.level,
                  room_id: room.id,
                  room_name: roomName,
                });
              }
              if (node.children && node.children.length > 0) {
                collectNodes(node.children, currentPath);
              }
            }
          };
          collectNodes(tree.zones || []);
          collectNodes(tree.storage_tree || []);
        }
        setStorageAddresses(shelves);
      } catch (e) {
        console.error('[EditAssetForm] Error loading storage addresses:', e);
      }
    };
    loadStorageAddresses();
  }, []);

  // Вспомогательные функции для обработки данных
  const flattenRooms = (tree: any[]) => {
    const rooms: Array<{ id: number; deptId: number; deptName: string; deptCode: string; roomId: number; roomName: string; fullName: string }> = [];
    try {
      const safeTree = Array.isArray(tree) ? tree : [];
      safeTree.forEach(dept => {
        if (!dept || typeof dept !== 'object') return;
        const roomsArr = Array.isArray(dept.rooms) ? dept.rooms : [];
        roomsArr.forEach((room: any) => {
          if (!room || typeof room !== 'object') return;
          let loc = room.name || '';
          if (room.floor) loc += ` - ${room.floor}`;
          if (room.building) loc += ` (${room.building})`;
          rooms.push({
            id: dept.id,
            deptId: dept.id,
            deptName: dept.name || '',
            deptCode: dept.code || '',
            roomId: room.id,
            roomName: room.name || '',
            fullName: `${dept.name || ''} - ${loc}`,
          });
        });
      });
    } catch (e) {
      console.error('flattenRooms error:', e);
    }
    return rooms;
  };

  const flattenEmployees = () => {
    try {
      const safeEmps = Array.isArray(employees) ? employees : [];
      return safeEmps.map((emp: any) => ({
        id: emp.id,
        name: emp.full_name || `${emp.last_name || ''} ${emp.first_name || ''}`,
        departmentName: emp.department_name || emp.department_code || '',
        fullName: `${emp.full_name || emp.last_name || ''} ${emp.first_name || ''}${emp.department_name ? ` (${emp.department_name})` : ''}`,
      }));
    } catch (e) {
      console.error('flattenEmployees error:', e);
      return [];
    }
  };

  const allRooms = flattenRooms(deptTree);
  const allEmployees = flattenEmployees();

  // Фильтрация по поиску (кабинеты + склады)
  const filteredLocations = useMemo(() => [
    ...allRooms.filter(r =>
      r.fullName.toLowerCase().includes(locationSearchQuery.toLowerCase())
    ).map(r => ({ id: `room_${r.roomId}`, name: r.fullName, type: 'room', roomId: r.roomId, deptCode: r.deptCode, searchKey: r.fullName.toLowerCase() })),
    ...storageAddresses.filter(sa =>
      sa.full_address.toLowerCase().includes(locationSearchQuery.toLowerCase()) ||
      sa.name.toLowerCase().includes(locationSearchQuery.toLowerCase()) ||
      sa.room_name?.toLowerCase().includes(locationSearchQuery.toLowerCase())
    ).map(sa => ({ id: `storage_${sa.id}`, name: sa.full_address, type: 'storage', storageId: sa.id, searchKey: sa.full_address.toLowerCase() })),
  ], [allRooms, storageAddresses, locationSearchQuery]);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<any>({
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
      quantity: existingAsset.quantity || 1,
      status: existingAsset.status,
      location_address: existingAsset.location_address || '',
      responsible_person: existingAsset.responsible_person || '',
      department_code: existingAsset.department_code || '',
      employee_id: existingAsset.assigned_employee_id || existingAsset.employee_id || null,
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
      rfid_tag: existingAsset.rfid_tag || '',
      storage_address_id: existingAsset.storage_address_id || undefined,
      storage_address_name: existingAsset.storage_address_name || '',
    },
  });

  const watchAssetType = watch('asset_type');

  useEffect(() => {
    const token = localStorage.getItem('token');
    fetch('/api/asset-types', {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {},
    })
      .then(async (r) => {
        if (!r.ok) {
          console.error('Failed to fetch asset-types:', r.status, await r.text());
          return [];
        }
        const text = await r.text();
        try {
          return JSON.parse(text);
        } catch {
          console.error('Invalid JSON from asset-types:', text);
          return [];
        }
      })
      .then(setAssetTypes)
      .catch(console.error);
  }, []);

  useEffect(() => {
    const initialType = existingAsset.asset_type || '';
    setSelectedType(initialType);
    if (initialType && assetTypes.length > 0) {
      const typeConfig = assetTypes.find(t => t.code === initialType);
      if (typeConfig && typeConfig.default_depreciation_years) {
        try { setValue('depreciation_years', typeConfig.default_depreciation_years); } catch(e) {}
      }
    }
  }, [existingAsset, assetTypes, setValue]);

  useEffect(() => {
    if (watchAssetType) {
      setSelectedType(watchAssetType);
      const typeConfig = assetTypes.find(t => t.code === watchAssetType);
      if (typeConfig && typeConfig.default_depreciation_years) {
        setValue('depreciation_years', typeConfig.default_depreciation_years);
      }
    }
  }, [watchAssetType, assetTypes]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    Promise.all([
      fetch('/api/admin/placements/tree', { headers: { 'Authorization': `Bearer ${token}` } }).then(r => {
        if (!r.ok) return [];
        return r.json();
      }).catch(() => []),
      fetch('/api/admin/placement-assignments/employees', { headers: { 'Authorization': `Bearer ${token}` } }).then(r => {
        if (!r.ok) return [];
        return r.json();
      }).catch(() => []),
      fetch('/api/admin/placement-assignments/responsible-persons', { headers: { 'Authorization': `Bearer ${token}` } }).then(r => {
        if (!r.ok) return [];
        return r.json();
      }).catch(() => []),
    ]).then(([tree, emps, responsibleUsers]) => {
      const safeTree = Array.isArray(tree) ? tree : [];
      const safeEmps = Array.isArray(emps) ? emps : [];
      const safeResponsibleUsers = Array.isArray(responsibleUsers) ? responsibleUsers : [];
      setDeptTree(safeTree);
      setEmployees(safeEmps);
      setLoadingOptions(false);
      
      if (existingAsset.department_code || existingAsset.location_address) {
        const rooms = flattenRooms(safeTree);
        const matchedRoom = rooms.find(r => 
          r.deptCode === existingAsset.department_code && r.fullName === existingAsset.location_address
        );
        if (matchedRoom) {
          setSelectedRoomId(matchedRoom.roomId);
        }
      }
      if (existingAsset.responsible_person) {
        const matchedUser = safeResponsibleUsers.find((u: any) => {
          const name = u.name || '';
          return (existingAsset.responsible_person || '').includes(name) || name.includes((existingAsset.responsible_person || '').split(' ')[0]);
        });
        if (matchedUser) {
          setSelectedResponsibleId(matchedUser.id);
        }
      }
      setResponsibleOptions(safeResponsibleUsers.map((u: any) => ({
        id: u.id,
        name: u.name,
        fullName: u.full_name,
      })));
      const empIdToUse = existingAsset.assigned_employee_id ?? existingAsset.employee_id;
      if (empIdToUse) {
        const matchedAssetEmp = safeEmps.find((emp: any) => emp.id === empIdToUse);
        if (matchedAssetEmp) {
          setSelectedEmployeeId(matchedAssetEmp.id);
        }
      }
      if (existingAsset.storage_address_id) {
        setSelectedStorageAddressId(existingAsset.storage_address_id);
      }
    }).catch(() => {
      console.error('Ошибка загрузки опций');
      setDeptTree([]);
      setEmployees([]);
      setResponsibleOptions([]);
      setLoadingOptions(false);
    });
  }, []);

  // Фильтрация кабинетов по номеру
  const [roomFilter, setRoomFilter] = useState('');
  const filteredRooms = allRooms.filter(r =>
    r.roomName.toLowerCase().includes(roomFilter.toLowerCase()) ||
    r.fullName.toLowerCase().includes(roomFilter.toLowerCase()) ||
    r.roomName.replace(/\D/g, '').includes(roomFilter)
  );

  // Объединённый список мест хранения: кабинеты + складские локации
  const allLocations = [
    ...allRooms.map(r => ({ id: `room_${r.roomId}`, name: r.fullName, type: 'room', roomId: r.roomId, deptCode: r.deptCode })),
    ...storageAddresses.map(sa => ({ id: `storage_${sa.id}`, name: sa.full_address, type: 'storage', storageId: sa.id })),
  ];

  // Определяем начальный тип расположения
  useEffect(() => {
    if (existingAsset.storage_address_id) {
      setSelectedLocationType('storage');
      setSelectedStorageAddressId(existingAsset.storage_address_id);
    } else if (existingAsset.department_code || existingAsset.location_address) {
      setSelectedLocationType('room');
    }
  }, []);

  const handleSubmitForm = async (data: any) => {
    try {
      const payload: Asset = {
        id: existingAsset.id,
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
        purchase_date: data.purchase_date || undefined,
        commissioning_date: data.commissioning_date || undefined,
        warranty_expiry: data.warranty_expiry || undefined,
        serial_number: data.serial_number,
        capacity: data.capacity ? Number(data.capacity) : undefined,
        power: data.power,
        weight: data.weight,
        consumable_type: data.consumable_type,
        crypto_wallet_address: data.crypto_wallet_address,
        crypto_token_symbol: data.crypto_token_symbol,
        depreciation_years: data.depreciation_years ? Number(data.depreciation_years) : undefined,
        next_maintenance_date: data.next_maintenance_date || undefined,
        rfid_tag: data.rfid_tag || '',
        storage_address_id: selectedStorageAddressId ? Number(selectedStorageAddressId) : null,
        employee_id: selectedEmployeeId ? Number(selectedEmployeeId) : null,
        is_active: existingAsset.is_active,
        created_at: existingAsset.created_at,
        updated_at: new Date().toISOString(),
      };
      await onSubmit(payload);
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
                setSelectedType(e.target.value);
                const typeConfig = assetTypes.find(t => t.code === e.target.value);
                if (typeConfig && typeConfig.default_depreciation_years && !existingAsset.depreciation_years) {
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
              })}
                              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="1"
            />
          </div>
        </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
          Статус *
        </label>
        <select
          {...register('status', {
            required: 'Обязательное поле',
          })}
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

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
            Место хранения
          </label>
          <div className="location-search-container relative">
            <input
              type="text"
              value={locationSearchQuery}
              onChange={(e) => {
                setLocationSearchQuery(e.target.value);
                setLocationDropdownOpen(true);
                if (selectedLocationType) {
                  setSelectedLocationType('');
                  setSelectedRoomId('');
                  setSelectedStorageAddressId('');
                  setValue('department_code', '');
                  setValue('location_address', '');
                  setValue('storage_address_id', undefined);
                  setValue('storage_address_name', '');
                }
              }}
              onFocus={() => setLocationDropdownOpen(true)}
              placeholder="Поиск по локации..."
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {locationDropdownOpen && (
              <div className="absolute z-50 mt-1 w-full max-h-60 overflow-y-auto bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg">
                {filteredLocations.length === 0 ? (
                  <div className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                    {locationSearchQuery ? 'Ничего не найдено' : 'Нет доступных мест хранения'}
                  </div>
                ) : (
                  <div className="divide-y divide-gray-100 dark:divide-gray-700">
                    {filteredLocations.filter(l => l.type === 'room').length > 0 && (
                      <div className="px-3 py-1.5 text-xs font-semibold text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-900">
                        Кабинеты
                      </div>
                    )}
                    {filteredLocations.filter(l => l.type === 'room').map(loc => (
                      <div
                        key={loc.id}
                        onClick={() => {
                          const roomId = Number(loc.id.replace('room_', ''));
                          setSelectedLocationType('room');
                          setSelectedRoomId(roomId);
                          setSelectedStorageAddressId('');
                          const room = allRooms.find(r => r.roomId === roomId);
                          if (room) {
                            setValue('department_code', room.deptCode);
                            setValue('location_address', room.fullName);
                            setValue('storage_address_id', undefined);
                            setValue('storage_address_name', '');
                          }
                          setLocationSearchQuery(room.fullName);
                          setLocationDropdownOpen(false);
                        }}
                        className="px-4 py-2.5 hover:bg-blue-50 dark:hover:bg-blue-900/20 cursor-pointer text-sm text-gray-900 dark:text-gray-100"
                      >
                        {loc.name}
                      </div>
                    ))}
                    {filteredLocations.filter(l => l.type === 'storage').length > 0 && (
                      <div className="px-3 py-1.5 text-xs font-semibold text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-900">
                        Складские локации
                      </div>
                    )}
                    {filteredLocations.filter(l => l.type === 'storage').map(loc => {
                      const storageId = Number(loc.id.replace('storage_', ''));
                      const sa = storageAddresses.find(s => s.id === storageId);
                      const locationName = sa?.full_address || loc.name;
                      return (
                        <div
                          key={loc.id}
                          onClick={() => {
                            setSelectedLocationType('storage');
                            setSelectedStorageAddressId(storageId);
                            setSelectedRoomId('');
                            setValue('storage_address_id', storageId);
                            setValue('storage_address_name', locationName);
                            setValue('department_code', '');
                            // Полный адрес склада пишем в location_address,
                            // иначе в списке активов местоположение показывается как «—»
                            setValue('location_address', locationName);
                            setLocationSearchQuery(locationName);
                            setLocationDropdownOpen(false);
                          }}
                          className="px-4 py-2.5 hover:bg-blue-50 dark:hover:bg-blue-900/20 cursor-pointer text-sm text-gray-900 dark:text-gray-100"
                        >
                          {loc.name}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
          {allRooms.length === 0 && storageAddresses.length === 0 && !loadingOptions && (
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Нет доступных мест хранения</p>
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
        <div className="flex gap-2">
          <input
            type="text"
            {...register('rfid_tag')}
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Уникальный ID RFID-метки (для сканера)"
          />
          {existingAsset.rfid_tag && (
            <button
              type="button"
              onClick={() => setValue('rfid_tag', '')}
              className="px-3 py-2 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 border border-red-300 dark:border-red-700 rounded-lg hover:bg-red-200 dark:hover:bg-red-900/50 transition text-sm whitespace-nowrap"
              title="Очистить RFID-метку"
            >
              ✕ Очистить
            </button>
          )}
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Если заполнено, RFID-сканер сможет находить этот актив по метке
        </p>
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
            'Сохранить'
          )}
        </button>
      </div>
    </form>
  );
};

export default EditAssetForm;
