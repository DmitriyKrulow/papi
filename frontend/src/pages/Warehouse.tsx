// frontend/src/pages/Warehouse.tsx
import { useState, useEffect, useCallback } from 'react';
import { Boxes, Loader2, Building2, Grid3X3, Package, ChevronRight, ChevronDown, Archive, Layers, MapPin } from 'lucide-react';
import toast from 'react-hot-toast';

interface WarehouseRoom {
  id: number;
  name: string;
  floor?: string;
  building?: string;
  department_id: number;
  department_name: string;
  full_name: string;
  cell_count?: number;
}

interface StorageAddressNode {
  id: number;
  name: string;
  type: 'rack' | 'shelf' | 'cell';
  parent_id: number | null;
  current_count?: number;
  capacity?: number;
  children?: StorageAddressNode[];
}

interface Asset {
  id: number;
  name: string;
  inventory_number?: string;
  storage_address_id?: number | null;
  storage_address_name?: string;
  [key: string]: any;
}

interface MoveModalState {
  isOpen: boolean;
  asset: Asset | null;
  destinationCells: StorageAddressNode[];
  loading: boolean;
  selectedCellId: number | null;
}

const Warehouse: React.FC = () => {
  const [rooms, setRooms] = useState<WarehouseRoom[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRoomId, setSelectedRoomId] = useState<number | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [storageTree, setStorageTree] = useState<StorageAddressNode[]>([]);
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

  const fetchStorageTree = useCallback(async (roomId: number) => {
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
        const treeData = Array.isArray(data) ? data : (data.tree || []);
        setStorageTree(treeData);
        // Auto-expand first level (racks)
        const initialExpanded = new Set<string>(
          treeData.map((node: StorageAddressNode) => String(node.id))
        );
        setExpandedNodes(initialExpanded);
      } else {
        toast.error(`Ошибка загрузки дерева склада (${response.status})`);
      }
    } catch (err: any) {
      toast.error(err.message || 'Ошибка соединения с сервером');
    } finally {
      setTreeLoading(false);
    }
  }, []);

  const handleRoomClick = (roomId: number) => {
    if (selectedRoomId === roomId) {
      setSelectedRoomId(null);
      setStorageTree([]);
      setExpandedNodes(new Set());
    } else {
      setSelectedRoomId(roomId);
      fetchStorageTree(roomId);
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
      const token = localStorage.getItem('token') || '';
      let cells: StorageAddressNode[] = [];

      if (addressId) {
        // Fetch cells from the same storage address tree
        const response = await fetch(`/api/storage-addresses/${addressId}/assets`, {
          headers: {
            'Authorization': token ? `Bearer ${token}` : '',
            'Content-Type': 'application/json',
          },
        });
        if (response.ok) {
          // We'll load cells from the room's tree instead
        }
      }

      // Load all cells from all rooms in the tree
      if (selectedRoomId) {
        const response = await fetch(`/api/storage-addresses/rooms/${selectedRoomId}/tree`, {
          headers: {
            'Authorization': token ? `Bearer ${token}` : '',
            'Content-Type': 'application/json',
          },
        });
        if (response.ok) {
          const treeData = await response.json();
          const tree = Array.isArray(treeData) ? treeData : (treeData.tree || []);
          // Flatten all cells from tree
          const flattenCells = (nodes: StorageAddressNode[]): StorageAddressNode[] => {
            let result: StorageAddressNode[] = [];
            for (const node of nodes) {
              if (node.type === 'cell') {
                result.push(node);
              }
              if (node.children) {
                result = result.concat(flattenCells(node.children));
              }
            }
            return result;
          };
          cells = flattenCells(tree);
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
  }, [selectedRoomId]);

  // Handle move asset
  const handleMoveAsset = useCallback(async () => {
    if (!moveModal.asset || !moveModal.selectedCellId) {
      toast.error('Выберите ячейку для перемещения');
      return;
    }
    try {
      const token = localStorage.getItem('token') || '';
      const response = await fetch(`/api/assets/${moveModal.asset.id}`, {
        method: 'PATCH',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          storage_address_id: moveModal.selectedCellId,
        }),
      });

      if (response.ok) {
        toast.success(`Актив перемещён в ячейку`);
        setMoveModal({ isOpen: false, asset: null, destinationCells: [], loading: false, selectedCellId: null });
        // Refresh search results if search is active
        if (searchQuery.trim()) {
          await searchAssets(searchQuery);
        }
        // Refresh room data
        fetchWarehouseData();
      } else {
        const errData = await response.json().catch(() => ({}));
        toast.error(errData.detail || `Ошибка перемещения (${response.status})`);
      }
    } catch (err: any) {
      toast.error(err.message || 'Ошибка соединения с сервером');
    }
  }, [moveModal.asset, moveModal.selectedCellId, searchQuery, searchAssets, fetchWarehouseData]);

  const openMoveModal = useCallback((asset: Asset) => {
    loadDestinationCells(asset.storage_address_id || null);
    setMoveModal((prev) => ({ ...prev, isOpen: true, asset, destinationCells: [], loading: false, selectedCellId: null }));
  }, [loadDestinationCells]);

  const closeMoveModal = useCallback(() => {
    setMoveModal({ isOpen: false, asset: null, destinationCells: [], loading: false, selectedCellId: null });
  }, []);

  // Статистика
  const totalRooms = rooms.length;
  const totalCells = rooms.reduce((sum, room) => sum + (room.cell_count || 0), 0);
  const totalAssets = rooms.reduce((sum, room) => {
    // Если в ответе есть поле с количеством активов — используем его
    // Иначе оцениваем по количеству помещений (заглушка)
    return sum + (room as any).asset_count || 0;
  }, 0);

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
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Управление помещениями и ячейками склада</p>
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
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Total rooms */}
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

        {/* Total cells */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-5">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-green-50 dark:bg-green-900/20">
              <Grid3X3 className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{totalCells}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Всего ячеек</p>
            </div>
          </div>
        </div>

        {/* Assets on warehouse */}
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
                onClick={() => handleRoomClick(room.id)}
                className={`px-5 py-3.5 hover:bg-gray-50 dark:hover:bg-gray-750 transition cursor-pointer ${
                  selectedRoomId === room.id ? 'bg-blue-50 dark:bg-blue-900/10 border-l-4 border-l-blue-500' : 'border-l-4 border-l-transparent'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{room.full_name}</p>
                    <div className="flex items-center gap-3 mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                      {room.floor && <span>Этаж: {room.floor}</span>}
                      {room.building && <span>Здание: {room.building}</span>}
                      {room.department_name && <span>{room.department_name}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 ml-4">
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                      <Grid3X3 className="w-3 h-3" />
                      {room.cell_count || 0} ячеек
                    </span>
                    <ChevronRight className={`w-4 h-4 text-gray-400 transition-transform ${selectedRoomId === room.id ? 'rotate-90' : ''}`} />
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

      {/* Storage Address Tree */}
      {selectedRoomId && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <Archive className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              Структура склада
            </h2>
            <button
              onClick={() => {
                setSelectedRoomId(null);
                setStorageTree([]);
                setExpandedNodes(new Set());
              }}
              className="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition"
            >
              Закрыть
            </button>
          </div>
          {treeLoading ? (
            <div className="px-5 py-12 text-center">
              <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2 text-blue-600 dark:text-blue-400" />
              <p className="text-gray-500 dark:text-gray-400 text-sm">Загрузка структуры...</p>
            </div>
          ) : storageTree.length === 0 ? (
            <div className="px-5 py-12 text-center">
              <Layers className="w-10 h-10 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
              <p className="text-gray-500 dark:text-gray-400 text-sm">Структура склада пуста</p>
            </div>
          ) : (
            <div className="px-5 py-3">
              {storageTree.map((rack) => (
                <StorageTreeNode
                  key={rack.id}
                  node={rack}
                  depth={0}
                  expandedNodes={expandedNodes}
                  onToggle={toggleNode}
                />
              ))}
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

// Recursive tree node component
interface StorageTreeNodeProps {
  node: StorageAddressNode;
  depth: number;
  expandedNodes: Set<string>;
  onToggle: (nodeId: string) => void;
}

const StorageTreeNode: React.FC<StorageTreeNodeProps> = ({ node, depth, expandedNodes, onToggle }) => {
  const hasChildren = node.children && node.children.length > 0;
  const isExpanded = expandedNodes.has(String(node.id));
  const isCell = node.type === 'cell';

  const iconMap = {
    rack: <Archive className="w-4 h-4 text-amber-600 dark:text-amber-400" />,
    shelf: <Layers className="w-4 h-4 text-blue-600 dark:text-blue-400" />,
    cell: <MapPin className="w-4 h-4 text-green-600 dark:text-green-400" />,
  };

  const labelMap = {
    rack: 'Стеллаж',
    shelf: 'Полка',
    cell: 'Ячейка',
  };

  return (
    <div className="select-none">
      <div
        className={`flex items-center gap-2 py-1.5 px-2 rounded-md hover:bg-gray-50 dark:hover:bg-gray-750 transition cursor-pointer ${
          isCell ? 'pl-6' : ''
        }`}
        style={{ paddingLeft: `${depth * 24 + 8}px` }}
        onClick={() => {
          if (hasChildren) {
            onToggle(String(node.id));
          }
        }}
      >
        {/* Expand / Collapse toggle */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (hasChildren) {
              onToggle(String(node.id));
            }
          }}
          className={`w-5 h-5 flex items-center justify-center rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition ${
            hasChildren ? 'cursor-pointer' : 'cursor-default opacity-0'
          }`}
        >
          {isExpanded ? (
            <ChevronDown className="w-3.5 h-3.5 text-gray-500" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 text-gray-500" />
          )}
        </button>

        {/* Icon */}
        <span className="flex-shrink-0">{iconMap[node.type]}</span>

        {/* Label */}
        <span className={`text-sm truncate flex-1 ${isCell ? 'text-gray-700 dark:text-gray-300' : 'text-gray-900 dark:text-gray-100 font-medium'}`}>
          {node.name}
        </span>

        {/* Cell stats */}
        {isCell && (
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {node.current_count ?? 0}/{node.capacity ?? 0}
            </span>
            {node.capacity && node.current_count !== undefined && (
              <span className="text-xs px-1.5 py-0.5 rounded-full font-medium"
                style={{
                  backgroundColor: node.capacity > 0
                    ? `${Math.min(100, Math.round(((node.current_count || 0) / node.capacity) * 100))}%` === '100'
                      ? 'rgba(239, 68, 68, 0.15)'
                      : Math.round(((node.current_count || 0) / node.capacity) * 100) > 70
                        ? 'rgba(245, 158, 11, 0.15)'
                        : 'rgba(34, 197, 94, 0.15)'
                    : 'rgba(34, 197, 94, 0.15)',
                  color: node.capacity > 0
                    ? `${Math.min(100, Math.round(((node.current_count || 0) / node.capacity) * 100))}%` === '100'
                      ? '#ef4444'
                      : Math.round(((node.current_count || 0) / node.capacity) * 100) > 70
                        ? '#f59e0b'
                        : '#22c55e'
                    : '#22c55e',
                }}
              >
                {node.capacity > 0 ? Math.round(((node.current_count || 0) / node.capacity) * 100) : 0}%
              </span>
            )}
          </div>
        )}
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div className="border-l border-gray-200 dark:border-gray-700 ml-4">
          {node.children!.map((child) => (
            <StorageTreeNode
              key={child.id}
              node={child}
              depth={depth + 1}
              expandedNodes={expandedNodes}
              onToggle={onToggle}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Warehouse;
