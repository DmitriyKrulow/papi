// frontend/src/pages/Warehouse.tsx
import { useState, useEffect, useCallback } from 'react';
import { Boxes, Loader2, Building2, Package, ChevronRight, ChevronDown, Archive, Layers, MapPin, Plus, Trash2, X, Pencil, Copy, FolderPlus, MoveRight } from 'lucide-react';
import toast from 'react-hot-toast';

interface WarehouseRoom {
  id: number;
  name: string;
  floor?: string;
  building?: string;
  department_id: number;
  department_name: string;
  full_name: string;
  asset_count: number;
  storage_addresses_count: number;
}

interface WarehouseTreeNode {
  id: number;
  name: string;
  code?: string;
  level: 'zone' | 'rack' | 'shelf' | 'asset';
  parent_id?: number | null;
  current_count?: number;
  capacity?: number;
  children?: WarehouseTreeNode[];
  is_zone?: boolean;
  location_type?: string;
  inventory_number?: string;
  room_id?: number;
}

interface Asset {
  id: number;
  name: string;
  inventory_number?: string;
  storage_address_id?: number | null;
  storage_address_name?: string;
  warehouse_location_id?: number | null;
  room_id?: number | null;
  [key: string]: any;
}

interface MoveModalState {
  isOpen: boolean;
  asset: Asset | null;
  destinationCells: WarehouseTreeNode[];
  loading: boolean;
  selectedCellId: number | null;
}

interface AddAddressModal {
  isOpen: boolean;
  mode: 'zone' | 'rack' | 'shelf';
  parentId: number | null;
  parentName: string;
  loading: boolean;
}

interface RenameModal {
  isOpen: boolean;
  nodeId: number | null;
  nodeName: string;
  nodeLevel: string;
  loading: boolean;
}

const Warehouse: React.FC = () => {
  const [rooms, setRooms] = useState<WarehouseRoom[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRoom, setSelectedRoom] = useState<WarehouseRoom | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [treeData, setTreeData] = useState<{
    zones: WarehouseTreeNode[];
    storage_tree: WarehouseTreeNode[];
    unassigned_assets: WarehouseTreeNode[];
  } | null>(null);
  const [treeLoading, setTreeLoading] = useState<boolean>(false);

  // Search state
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<Asset[]>([]);
  const [searchLoading, setSearchLoading] = useState<boolean>(false);
  const [showSearchResults, setShowSearchResults] = useState<boolean>(false);

  // Move modal state
  const [moveModal, setMoveModal] = useState<MoveModalState>({
    isOpen: false,
    asset: null,
    destinationCells: [],
    loading: false,
    selectedCellId: null,
  });

  // Add address modal state
  const [addAddressModal, setAddAddressModal] = useState<AddAddressModal>({
    isOpen: false,
    mode: 'rack',
    parentId: null,
    parentName: '',
    loading: false,
  });
  const [newAddressName, setNewAddressName] = useState('');
  const [newAddressCapacity, setNewAddressCapacity] = useState<number | ''>('');

  // Rename modal state
  const [renameModal, setRenameModal] = useState<RenameModal>({
    isOpen: false,
    nodeId: null,
    nodeName: '',
    nodeLevel: '',
    loading: false,
  });
  const [renameValue, setRenameValue] = useState('');

  const fetchWarehouseData = useCallback(async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token') || '';
      const response = await fetch('/api/storage-addresses/rooms/all?room_type=warehouse', {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        const roomsData = Array.isArray(data) ? data : (data.items || []);
        setRooms(roomsData);
        setError(null);
      } else {
        const errMsg = `Ошибка загрузки данных склада (${response.status})`;
        setError(errMsg);
        toast.error(errMsg);
      }
    } catch (err: any) {
      const errMsg = err.message || 'Ошибка соединения с сервером';
      setError(errMsg);
      toast.error(errMsg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWarehouseData();
  }, [fetchWarehouseData]);

  const fetchTreeData = useCallback(async (roomId: number) => {
    try {
      setTreeLoading(true);
      const token = localStorage.getItem('token') || '';
      const response = await fetch(`/api/storage-addresses/rooms/${roomId}/tree`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setTreeData({
          zones: data.zones || [],
          storage_tree: data.storage_tree || [],
          unassigned_assets: data.unassigned_assets || [],
        });
        // Auto-expand zones and root items
        const allIds = [
          ...(data.zones || []).map((n: any) => String(n.id)),
          ...(data.storage_tree || []).map((n: any) => String(n.id)),
        ];
        setExpandedNodes(new Set(allIds));
      } else {
        toast.error(`Ошибка загрузки дерева склада (${response.status})`);
      }
    } catch (err: any) {
      toast.error(err.message || 'Ошибка соединения с сервером');
    } finally {
      setTreeLoading(false);
    }
  }, []);

  const handleRoomClick = (room: WarehouseRoom) => {
    if (selectedRoom?.id === room.id) {
      setSelectedRoom(null);
      setTreeData(null);
      setExpandedNodes(new Set());
    } else {
      setSelectedRoom(room);
      fetchTreeData(room.id);
    }
  };

  const toggleNode = (nodeId: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  };

  // Flatten all cells from tree for move modal
  const flattenCells = (nodes: WarehouseTreeNode[]): WarehouseTreeNode[] => {
    let result: WarehouseTreeNode[] = [];
    for (const node of nodes) {
      if (node.level === 'shelf') {
        result.push(node);
      }
      if (node.children) {
        result = result.concat(flattenCells(node.children));
      }
    }
    return result;
  };

  // Collect all assignable nodes (zones + cells)
  const getAllAssignableNodes = (data: typeof treeData): WarehouseTreeNode[] => {
    if (!data) return [];
    const all: WarehouseTreeNode[] = [];
    // Zones are assignable
    data.zones?.forEach(z => all.push(z));
    // Cells from storage_tree
    const cells = flattenCells(data.storage_tree || []);
    all.push(...cells);
    // Cells from zones (nested storage addresses)
    data.zones?.forEach(z => {
      if (z.children) {
        all.push(...flattenCells(z.children));
      }
    });
    return all;
  };

  // Rename functions
  const openRenameModal = useCallback((node: WarehouseTreeNode) => {
    setRenameModal({
      isOpen: true,
      nodeId: node.id,
      nodeName: node.name,
      nodeLevel: node.level,
      loading: false,
    });
    setRenameValue(node.name);
  }, []);

  const closeRenameModal = useCallback(() => {
    setRenameModal({ isOpen: false, nodeId: null, nodeName: '', nodeLevel: '', loading: false });
    setRenameValue('');
  }, []);

  const handleRename = useCallback(async () => {
    if (!renameValue.trim() || !renameModal.nodeId) {
      toast.error('Введите название');
      return;
    }
    try {
      setRenameModal(prev => ({ ...prev, loading: true }));
      const token = localStorage.getItem('token') || '';
      
      // Determine if it's a zone (warehouse_location) or storage_address
      const isZone = renameModal.nodeLevel === 'zone' && treeData?.zones?.some(z => z.id === renameModal.nodeId);
      const endpoint = isZone
        ? `/api/storage-addresses/warehouse-locations/${renameModal.nodeId}`
        : `/api/storage-addresses/${renameModal.nodeId}`;
      const method = isZone ? 'PUT' : 'PATCH';
      
      let response;
      if (isZone) {
        response = await fetch(`${endpoint}?name=${encodeURIComponent(renameValue.trim())}`, {
          headers: { 'Authorization': token ? `Bearer ${token}` : '' },
        });
      } else {
        response = await fetch(endpoint, {
          method: 'PATCH',
          headers: {
            'Authorization': token ? `Bearer ${token}` : '',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ name: renameValue.trim() }),
        });
      }

      if (response.ok) {
        toast.success('Переименовано');
        closeRenameModal();
        if (selectedRoom) {
          await fetchTreeData(selectedRoom.id);
        }
      } else {
        const errData = await response.json().catch(() => ({}));
        toast.error(errData.detail || `Ошибка (${response.status})`);
      }
    } catch (err: any) {
      toast.error(err.message || 'Ошибка соединения');
    } finally {
      setRenameModal(prev => ({ ...prev, loading: false }));
    }
  }, [renameValue, renameModal, treeData, selectedRoom, closeRenameModal, fetchTreeData, selectedRoom]);

  // Search assets
  const searchAssets = useCallback(async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      setShowSearchResults(false);
      return;
    }
    try {
      setSearchLoading(true);
      const token = localStorage.getItem('token') || '';
      const response = await fetch(`/api/assets/?search=${encodeURIComponent(query)}`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        const assets = Array.isArray(data) ? data : (data.items || data.data || []);
        setSearchResults(assets);
        setShowSearchResults(true);
      } else {
        toast.error(`Ошибка поиска (${response.status})`);
      }
    } catch (err: any) {
      toast.error(err.message || 'Ошибка соединения с сервером');
    } finally {
      setSearchLoading(false);
    }
  }, []);

  // Load destination cells for move
  const loadDestinationCells = useCallback(async (addressId: number | null) => {
    try {
      setMoveModal((prev) => ({ ...prev, loading: true }));
      const t = localStorage.getItem('token') || '';
      let cells: WarehouseTreeNode[] = [];

      if (selectedRoom) {
        const response = await fetch(`/api/storage-addresses/rooms/${selectedRoom.id}/tree`, {
          headers: {
            'Authorization': t ? `Bearer ${t}` : '',
            'Content-Type': 'application/json',
          },
        });
        if (response.ok) {
          const data = await response.json();
          cells = getAllAssignableNodes({
            zones: data.zones || [],
            storage_tree: data.storage_tree || [],
            unassigned_assets: data.unassigned_assets || [],
          });
        }
      }

      setMoveModal((prev) => ({
        ...prev,
        destinationCells: cells,
        loading: false,
        selectedCellId: null,
      }));
    } catch (err: any) {
      toast.error(err.message || 'Ошибка загрузки ячеек');
      setMoveModal((prev) => ({ ...prev, loading: false }));
    }
  }, [selectedRoom]);

  // Handle move asset
  const handleMoveAsset = useCallback(async () => {
    if (!moveModal.asset || !moveModal.selectedCellId) {
      toast.error('Выберите ячейку для перемещения');
      return;
    }
    try {
      const t = localStorage.getItem('token') || '';
      const response = await fetch(`/api/assets/${moveModal.asset.id}`, {
        method: 'PATCH',
        headers: {
          'Authorization': t ? `Bearer ${t}` : '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          storage_address_id: moveModal.selectedCellId,
        }),
      });

      if (response.ok) {
        toast.success('Актив перемещён');
        setMoveModal({ isOpen: false, asset: null, destinationCells: [], loading: false, selectedCellId: null });
        if (searchQuery.trim()) {
          await searchAssets(searchQuery);
        }
        if (selectedRoom) {
          await fetchTreeData(selectedRoom.id);
        }
        fetchWarehouseData();
      } else {
        const errData = await response.json().catch(() => ({}));
        toast.error(errData.detail || `Ошибка перемещения (${response.status})`);
      }
    } catch (err: any) {
      toast.error(err.message || 'Ошибка соединения с сервером');
    }
  }, [moveModal.asset, moveModal.selectedCellId, searchQuery, searchAssets, fetchWarehouseData, fetchTreeData, selectedRoom]);

  const openMoveModal = useCallback((asset: Asset) => {
    loadDestinationCells(asset.storage_address_id || null);
    setMoveModal((prev) => ({ ...prev, isOpen: true, asset, destinationCells: [], loading: false, selectedCellId: null }));
  }, [loadDestinationCells]);

  const closeMoveModal = useCallback(() => {
    setMoveModal({ isOpen: false, asset: null, destinationCells: [], loading: false, selectedCellId: null });
  }, []);

  // Add address functions
  const openAddAddressModal = useCallback((mode: 'zone' | 'rack' | 'shelf', parentId: number | null = null, parentName: string = '') => {
    setAddAddressModal({ isOpen: true, mode, parentId, parentName, loading: false });
    setNewAddressName('');
    setNewAddressCapacity('');
  }, []);

  const closeAddAddressModal = useCallback(() => {
    setAddAddressModal({ isOpen: false, mode: 'rack', parentId: null, parentName: '', loading: false });
    setNewAddressName('');
    setNewAddressCapacity('');
  }, []);

  const handleAddAddress = useCallback(async () => {
    try {
      setAddAddressModal(prev => ({ ...prev, loading: true }));
      const t = localStorage.getItem('token') || '';
      
      const levelMap = { zone: 'zone', rack: 'rack', shelf: 'shelf' };
      const level = levelMap[addAddressModal.mode];
      
      if (!level) {
        toast.error('Не указан уровень хранения');
        setAddAddressModal(prev => ({ ...prev, loading: false }));
        return;
      }
      
      // If adding a zone, use warehouse_locations endpoint
      if (addAddressModal.mode === 'zone') {
        const response = await fetch(`/api/storage-addresses/warehouse-locations?name=${encodeURIComponent(newAddressName.trim())}&room_id=${selectedRoom?.id}`, {
          method: 'POST',
          headers: {
            'Authorization': t ? `Bearer ${t}` : '',
          },
        });
        
        if (response.ok) {
          toast.success('Зона добавлена');
          closeAddAddressModal();
          // Refresh tree data
          if (selectedRoom) {
            await fetchTreeData(selectedRoom.id);
          }
          fetchWarehouseData();
        } else {
          const errData = await response.json().catch(() => ({}));
          toast.error(errData.detail || `Ошибка (${response.status})`);
        }
      } else {
        // Add storage address
        const body: any = {
          name: newAddressName.trim() || "",
          level: level,
          room_id: selectedRoom?.id,
          capacity: newAddressCapacity || undefined,
        };
        
        // Определяем, как связывать узел
        if (addAddressModal.mode === 'rack') {
          // Стеллаж привязывается к зоне через warehouse_location_id
          if (addAddressModal.parentId) {
            body.warehouse_location_id = addAddressModal.parentId;
          }
        } else if (addAddressModal.mode === 'shelf') {
          // Полка привязывается к стеллажу через parent_id
          if (addAddressModal.parentId) {
            body.parent_id = addAddressModal.parentId;
          }
        }
        
        console.log('Creating storage address:', body);
        console.log('Mode:', addAddressModal.mode, 'ParentId:', addAddressModal.parentId);
        
        const response = await fetch('/api/storage-addresses', {
          method: 'POST',
          headers: {
            'Authorization': t ? `Bearer ${t}` : '',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(body),
        });

        if (response.ok) {
          toast.success('Элемент добавлен');
          closeAddAddressModal();
          if (selectedRoom) {
            await fetchTreeData(selectedRoom.id);
          }
          fetchWarehouseData();
        } else {
          const errData = await response.json().catch(() => ({}));
          toast.error(errData.detail || `Ошибка (${response.status})`);
        }
      }
    } catch (err: any) {
      toast.error(err.message || 'Ошибка соединения');
    } finally {
      setAddAddressModal(prev => ({ ...prev, loading: false }));
    }
  }, [newAddressName, newAddressCapacity, addAddressModal.mode, addAddressModal.parentId, selectedRoom, closeAddAddressModal, fetchTreeData, fetchWarehouseData]);

  const handleDeleteAddress = useCallback(async (nodeId: number, nodeLevel: string, parentNodeId: number | null = null) => {
    if (!confirm('Удалить элемент и все вложенные?')) return;

    try {
      const t = localStorage.getItem('token') || '';
      
      // Determine if it's a zone or storage_address
      const isZone = nodeLevel === 'zone' && treeData?.zones?.some(z => z.id === nodeId);
      const endpoint = isZone
        ? `/api/storage-addresses/warehouse-locations/${nodeId}`
        : `/api/storage-addresses/${nodeId}`;
      const method = isZone ? 'DELETE' : 'DELETE';
      
      const response = await fetch(endpoint, {
        method,
        headers: {
          'Authorization': t ? `Bearer ${t}` : '',
        },
      });

      if (response.ok) {
        toast.success('Элемент удалён');
        if (selectedRoom) {
          await fetchTreeData(selectedRoom.id);
        }
        fetchWarehouseData();
      } else {
        const errData = await response.json().catch(() => ({}));
        toast.error(errData.detail || `Ошибка (${response.status})`);
      }
    } catch (err: any) {
      toast.error(err.message || 'Ошибка соединения');
    }
  }, [selectedRoom, fetchTreeData, fetchWarehouseData, treeData]);

  // Статистика
  const totalRooms = rooms.length;
  const totalAssets = rooms.reduce((sum, room) => sum + (room.asset_count || 0), 0);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-24">
        <div className="text-center">
          <Loader2 className="w-10 h-10 animate-spin mx-auto mb-3 text-blue-600 dark:text-blue-400" />
          <p className="text-gray-500 dark:text-gray-400 text-sm">Загрузка данных склада...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
          <Boxes className="w-7 h-7 text-blue-600 dark:text-blue-400" />
          Склад
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Управление помещениями и структурой хранения</p>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg flex items-center gap-2">
          <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-5">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-blue-50 dark:bg-blue-900/20">
              <Building2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{totalRooms}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Всего помещений</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-5">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-purple-50 dark:bg-purple-900/20">
              <Package className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{totalAssets}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Активов на складе</p>
            </div>
          </div>
        </div>
      </div>

      {/* Rooms list */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Помещения</h2>
        </div>
        {rooms.length === 0 ? (
          <div className="px-5 py-12 text-center">
            <Boxes className="w-10 h-10 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
            <p className="text-gray-500 dark:text-gray-400 text-sm">Помещения не найдены</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {rooms.map((room) => (
              <div
                key={room.id}
                onClick={() => handleRoomClick(room)}
                className={`px-5 py-3.5 hover:bg-gray-50 dark:hover:bg-gray-750 transition cursor-pointer ${
                  selectedRoom?.id === room.id ? 'bg-blue-50 dark:bg-blue-900/10 border-l-4 border-l-blue-500' : 'border-l-4 border-l-transparent'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{room.full_name || room.name}</p>
                    <div className="flex items-center gap-3 mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                      {room.floor && <span>Этаж: {room.floor}</span>}
                      {room.building && <span>Здание: {room.building}</span>}
                      {room.department_name && <span>{room.department_name}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 ml-4">
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                      <Package className="w-3 h-3" />
                      {room.asset_count || 0} активов
                    </span>
                    <ChevronRight className={`w-4 h-4 text-gray-400 transition-transform ${selectedRoom?.id === room.id ? 'rotate-90' : ''}`} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Search Assets */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Поиск активов
          </h2>
        </div>
        <div className="px-5 py-4">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    searchAssets(searchQuery);
                  }
                }}
                placeholder="Поиск по названию или инвентарному номеру..."
                className="w-full px-4 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              />
              {searchLoading && (
                <Loader2 className="w-4 h-4 animate-spin absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" />
              )}
            </div>
            <button
              onClick={() => searchAssets(searchQuery)}
              disabled={searchLoading || !searchQuery.trim()}
              className="px-5 py-2.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded-lg transition flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Найти
            </button>
            {showSearchResults && searchResults.length > 0 && (
              <button
                onClick={() => {
                  setShowSearchResults(false);
                  setSearchResults([]);
                  setSearchQuery('');
                }}
                className="px-4 py-2.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Search Results */}
        {showSearchResults && (
          <div className="border-t border-gray-100 dark:border-gray-700">
            {searchLoading ? (
              <div className="px-5 py-8 text-center">
                <Loader2 className="w-6 h-6 animate-spin mx-auto text-blue-600 dark:text-blue-400" />
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">Поиск...</p>
              </div>
            ) : searchResults.length === 0 ? (
              <div className="px-5 py-8 text-center">
                <Package className="w-8 h-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
                <p className="text-sm text-gray-500 dark:text-gray-400">Ничего не найдено</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-700">
                <div className="px-5 py-2 text-xs text-gray-500 dark:text-gray-400">
                  Найдено: {searchResults.length}
                </div>
                {searchResults.map((asset) => (
                  <div
                    key={asset.id}
                    className="px-5 py-3 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-750 transition"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                        {asset.name || 'Без названия'}
                      </p>
                      <div className="flex items-center gap-3 mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                        {asset.inventory_number && (
                          <span>Инв. №: {asset.inventory_number}</span>
                        )}
                        {asset.storage_address_name && (
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            {asset.storage_address_name}
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => openMoveModal(asset)}
                      className="ml-4 flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-700 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/40 rounded-md transition flex-shrink-0"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                      </svg>
                      Переместить
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Add Address Modal */}
      {addAddressModal.isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={closeAddAddressModal} />
          <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-md overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Добавить {addAddressModal.mode === 'rack' ? 'стеллаж' : 'полка'}
              </h3>
              <button onClick={closeAddAddressModal} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="px-6 py-4">
              {addAddressModal.parentName && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
                  Родитель: <span className="font-medium text-gray-700 dark:text-gray-300">{addAddressModal.parentName}</span>
                </p>
              )}
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Название *</label>
                  <input
                    type="text"
                    value={newAddressName}
                    onChange={(e) => setNewAddressName(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAddAddress()}
                    placeholder="Введите название (например: Полка 1)"
                    className="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                    autoFocus
                  />
                </div>
                {(addAddressModal.mode === 'shelf') && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Вместимость</label>
                    <input
                      type="number"
                      value={newAddressCapacity}
                      onChange={(e) => setNewAddressCapacity(e.target.value ? Number(e.target.value) : '')}
                      placeholder="Не ограничено"
                      min="0"
                      className="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                    />
                  </div>
                )}
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
              <button
                onClick={closeAddAddressModal}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition"
              >
                Отмена
              </button>
              <button
                onClick={handleAddAddress}
                disabled={addAddressModal.loading || !newAddressName.trim()}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded-lg transition flex items-center gap-2"
              >
                <Loader2 className={`w-4 h-4 ${addAddressModal.loading ? 'animate-spin' : 'hidden'}`} />
                Добавить
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Warehouse Structure Tree */}
      {selectedRoom && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <Archive className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              Структура: {selectedRoom.name}
            </h2>
            <div className="flex items-center gap-2">
              <button
                onClick={() => openAddAddressModal('zone')}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition"
              >
                <Plus className="w-3.5 h-3.5" />
                Зона
              </button>
              <button
                onClick={() => {
                  setSelectedRoom(null);
                  setTreeData(null);
                  setExpandedNodes(new Set());
                }}
                className="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition"
              >
                Закрыть
              </button>
            </div>
          </div>
          {treeLoading ? (
            <div className="px-5 py-12 text-center">
              <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2 text-blue-600 dark:text-blue-400" />
              <p className="text-gray-500 dark:text-gray-400 text-sm">Загрузка структуры...</p>
            </div>
          ) : !treeData || (treeData.zones.length === 0 && treeData.storage_tree.length === 0 && treeData.unassigned_assets.length === 0) ? (
            <div className="px-5 py-12 text-center">
              <Layers className="w-10 h-10 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
              <p className="text-gray-500 dark:text-gray-400 text-sm">Структура склада пуста</p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Добавьте зону для начала</p>
            </div>
          ) : (
            <div className="px-5 py-3 space-y-4">
              {/* Zones */}
              {treeData.zones.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2 px-2">Зоны</h3>
                  {treeData.zones.map((zone) => (
                    <WarehouseTreeNode
                      key={zone.id}
                      node={zone}
                      depth={0}
                      expandedNodes={expandedNodes}
                      onToggle={toggleNode}
                      onDelete={handleDeleteAddress}
                      onRename={openRenameModal}
                      onAddChild={openAddAddressModal}
                      onMoveAsset={(asset: Asset) => openMoveModal(asset)}
                      treeData={treeData}
                      fetchTreeData={fetchTreeData}
                      selectedRoom={selectedRoom}
                      fetchWarehouseData={fetchWarehouseData}
                    />
                  ))}
                </div>
              )}

              {/* Unassigned storage addresses (not in zones) */}
              {treeData.storage_tree.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2 px-2">Стеллажи без зоны</h3>
                  {treeData.storage_tree.map((node) => (
                    <WarehouseTreeNode
                      key={node.id}
                      node={node}
                      depth={0}
                      expandedNodes={expandedNodes}
                      onToggle={toggleNode}
                      onDelete={handleDeleteAddress}
                      onAddChild={openAddAddressModal}
                      onMoveAsset={(asset: Asset) => openMoveModal(asset)}
                      treeData={treeData}
                      fetchTreeData={fetchTreeData}
                      selectedRoom={selectedRoom}
                      fetchWarehouseData={fetchWarehouseData}
                    />
                  ))}
                </div>
              )}

              {/* Unassigned Assets */}
              {treeData.unassigned_assets.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2 px-2 flex items-center gap-2">
                    <Package className="w-4 h-4" />
                    Нераспределённые активы ({treeData.unassigned_assets.length})
                  </h3>
                  {treeData.unassigned_assets.map((assetNode) => (
                    <WarehouseTreeNode
                      key={assetNode.id}
                      node={assetNode}
                      depth={0}
                      expandedNodes={expandedNodes}
                      onToggle={toggleNode}
                      onDelete={() => {}}
                      onAddChild={openAddAddressModal}
                      onMoveAsset={(a: Asset) => openMoveModal(a as Asset)}
                      treeData={treeData}
                      fetchTreeData={fetchTreeData}
                      selectedRoom={selectedRoom}
                      fetchWarehouseData={fetchWarehouseData}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Move Modal */}
      {moveModal.isOpen && moveModal.asset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={closeMoveModal}
          />
          {/* Modal */}
          <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-md overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                </svg>
                Переместить актив
              </h3>
              <button
                onClick={closeMoveModal}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Body */}
            <div className="px-6 py-4">
              {/* Asset info */}
              <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {moveModal.asset.name || 'Без названия'}
                </p>
                {moveModal.asset.inventory_number && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Инв. №: {moveModal.asset.inventory_number}
                  </p>
                )}
                {moveModal.asset.storage_address_name && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    Текущее место: {moveModal.asset.storage_address_name}
                  </p>
                )}
              </div>

              {/* Destination selector */}
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Целевая ячейка
              </label>
              {moveModal.loading ? (
                <div className="flex justify-center py-6">
                  <Loader2 className="w-6 h-6 animate-spin text-blue-600 dark:text-blue-400" />
                </div>
              ) : moveModal.destinationCells.length === 0 ? (
                <div className="text-center py-6">
                  <Package className="w-8 h-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
                  <p className="text-sm text-gray-500 dark:text-gray-400">Нет доступных ячеек</p>
                </div>
              ) : (
                <select
                  value={moveModal.selectedCellId || ''}
                  onChange={(e) =>
                    setMoveModal((prev) => ({
                      ...prev,
                      selectedCellId: e.target.value ? Number(e.target.value) : null,
                    }))
                  }
                  className="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                >
                  <option value="">Выберите ячейку...</option>
                  {moveModal.destinationCells.map((cell) => (
                    <option key={cell.id} value={cell.id}>
                      {cell.name}
                      {cell.current_count !== undefined && cell.capacity !== undefined
                        ? ` (${cell.current_count}/${cell.capacity})`
                        : ''}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
              <button
                onClick={closeMoveModal}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition"
              >
                Отмена
              </button>
              <button
                onClick={handleMoveAsset}
                disabled={!moveModal.selectedCellId}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded-lg transition flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                </svg>
                Переместить
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Helper functions for tree rendering
const getLevelLabel = (level: string): string => {
  const labels: Record<string, string> = {
    zone: 'Зона', rack: 'Стеллаж', shelf: 'Полка', asset: 'Актив',
  };
  return labels[level] || level;
};

const getLevelColor = (level: string): string => {
  const colors: Record<string, string> = {
    zone: 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20',
    rack: 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20',
    shelf: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20',
    asset: 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900/20',
  };
  return colors[level] || 'text-gray-600 dark:text-gray-400';
};

// Recursive warehouse tree node component
interface WarehouseTreeNodeProps {
  node: WarehouseTreeNode;
  depth: number;
  expandedNodes: Set<string>;
  onToggle: (nodeId: string) => void;
  onDelete: (nodeId: number, nodeLevel: string, parentId?: number | null) => void;
  onRename: (node: WarehouseTreeNode) => void;
  onAddChild: (mode: 'zone' | 'rack' | 'shelf', parentId: number, parentName: string) => void;
  onMoveAsset: (asset: Asset) => void;
  treeData: { zones: WarehouseTreeNode[]; storage_tree: WarehouseTreeNode[]; unassigned_assets: WarehouseTreeNode[] } | null;
  fetchTreeData: (roomId: number) => Promise<void>;
  selectedRoom: WarehouseRoom | null;
  fetchWarehouseData: () => Promise<void>;
}

const WarehouseTreeNode: React.FC<WarehouseTreeNodeProps> = ({
  node, depth, expandedNodes, onToggle, onDelete, onRename, onAddChild, onMoveAsset,
  treeData, fetchTreeData, selectedRoom, fetchWarehouseData,
}) => {
  const hasChildren = node.children && node.children.length > 0;
  const isExpanded = expandedNodes.has(String(node.id));
  const isAsset = node.level === 'asset';

  const handleRowClick = () => {
    if (hasChildren && !isAsset) {
      onToggle(String(node.id));
    } else if (isAsset) {
      const mockAsset: Asset = {
        id: node.id, name: node.name, inventory_number: node.inventory_number,
        room_id: selectedRoom?.id,
      };
      onMoveAsset(mockAsset);
    }
  };

  const handleMoveAssetFromNode = () => {
    const mockAsset: Asset = {
      id: node.id, name: node.name, inventory_number: node.inventory_number,
      room_id: selectedRoom?.id,
    };
    onMoveAsset(mockAsset);
  };

  return (
    <div className="select-none">
      <div
        className={`flex items-center gap-2 py-1.5 px-2 rounded-md hover:bg-gray-50 dark:hover:bg-gray-750 transition ${isAsset ? 'cursor-pointer' : hasChildren ? 'cursor-pointer' : ''}`}
        style={{ paddingLeft: `${depth * 24 + 8}px` }}
        onClick={handleRowClick}
      >
        <button
          onClick={(e) => { e.stopPropagation(); if (hasChildren && !isAsset) onToggle(String(node.id)); }}
          className={`w-5 h-5 flex items-center justify-center rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition flex-shrink-0 ${hasChildren && !isAsset ? 'cursor-pointer' : 'cursor-default opacity-0'}`}
        >
          {isExpanded ? <ChevronDown className="w-3.5 h-3.5 text-gray-500" /> : <ChevronRight className="w-3.5 h-3.5 text-gray-500" />}
        </button>

        <span className={`text-xs px-1.5 py-0.5 rounded font-medium flex-shrink-0 ${getLevelColor(node.level)}`}>
          {getLevelLabel(node.level)}
        </span>

        {node.level === 'zone' && <Building2 className="w-4 h-4 text-purple-600 dark:text-purple-400 flex-shrink-0" />}
        {node.level === 'rack' && <Archive className="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0" />}
        {node.level === 'shelf' && <Layers className="w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0" />}
        {node.level === 'asset' && <Package className="w-4 h-4 text-gray-600 dark:text-gray-400 flex-shrink-0" />}

        <span className={`text-sm truncate flex-1 ${isAsset ? 'text-gray-600 dark:text-gray-400 italic' : 'text-gray-900 dark:text-gray-100 font-medium'}`}>
          {node.name}
        </span>

        {(node.level === 'zone' || node.level === 'rack' || node.level === 'shelf') && node.current_count !== undefined && node.current_count > 0 && (
          <span className={`text-xs flex-shrink-0 ${
            node.level === 'zone' ? 'text-purple-600 dark:text-purple-400' :
            node.level === 'rack' ? 'text-amber-600 dark:text-amber-400' :
            'text-blue-600 dark:text-blue-400'
          }`}>
            {node.current_count} ак.
          </span>
        )}

        <div className="flex items-center gap-0.5 flex-shrink-0" onClick={(e) => e.stopPropagation()}>
          {!isAsset && (
            <button onClick={() => onRename(node)} className="p-1 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded transition" title="Переименовать">
              <Pencil className="w-3.5 h-3.5" />
            </button>
          )}
          {!isAsset && node.level === 'zone' && (
            <button onClick={() => onAddChild('rack', node.id, node.name)} className="p-1 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded transition" title="Добавить стеллаж">
              <Plus className="w-3.5 h-3.5" />
            </button>
          )}
          {!isAsset && node.level === 'rack' && (
            <button onClick={() => onAddChild('shelf', node.id, node.name)} className="p-1 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded transition" title="Добавить полку">
              <Plus className="w-3.5 h-3.5" />
            </button>
          )}
          {isAsset && (
            <button onClick={handleMoveAssetFromNode} className="p-1 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded transition" title="Переместить">
              <MoveRight className="w-3.5 h-3.5" />
            </button>
          )}
          {!isAsset && (
            <button onClick={() => onDelete(node.id, node.level, node.parent_id ?? null)} className="p-1 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition" title="Удалить">
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {hasChildren && isExpanded && (
        <div className="border-l border-gray-200 dark:border-gray-700 ml-4">
          {node.children!.map((child) => (
            <WarehouseTreeNode
              key={child.id} node={child} depth={depth + 1} expandedNodes={expandedNodes}
              onToggle={onToggle} onDelete={onDelete} onRename={onRename} onAddChild={onAddChild}
              onMoveAsset={onMoveAsset} treeData={treeData} fetchTreeData={fetchTreeData}
              selectedRoom={selectedRoom} fetchWarehouseData={fetchWarehouseData}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Warehouse;
