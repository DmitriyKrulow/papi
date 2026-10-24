// frontend/src/pages/Warehouse.tsx
import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';

interface WarehouseRoom {
  id: number;
  name: string;
  department_id: number;
  department_name: string;
  floor?: string;
  building?: string;
  room_type: string;
}

interface WarehouseLocation {
  id: number;
  name: string;
  code?: string;
  location_type: string;
  description?: string;
  room_id: number;
  room_name?: string;
  capacity?: number;
  current_count: number;
  storage_addresses_count?: number;
}

const Warehouse = () => {
  const { isAuthenticated } = useAuth();
  const [rooms, setRooms] = useState<WarehouseRoom[]>([]);
  const [locations, setLocations] = useState<WarehouseLocation[]>([]);
  const [selectedRoom, setSelectedRoom] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadRooms();
  }, []);

  useEffect(() => {
    if (selectedRoom) {
      loadLocations(selectedRoom);
    }
  }, [selectedRoom]);

  const loadRooms = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch('/api/storage-addresses/rooms', {
        headers: { 'Authorization': token ? `Bearer ${token}` : '' },
      });
      if (response.ok) {
        const data = await response.json();
        setRooms(data);
      }
    } catch (err) {
      setError('Ошибка загрузки складов');
    } finally {
      setLoading(false);
    }
  };

  const loadLocations = async (roomId: number) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/storage-addresses/warehouse-locations?room_id=${roomId}`, {
        headers: { 'Authorization': token ? `Bearer ${token}` : '' },
      });
      if (response.ok) {
        const data = await response.json();
        setLocations(data.locations || []);
      }
    } catch (err) {
      setError('Ошибка загрузки локаций');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">📦 Управление складами</h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Список складов */}
        <div className="md:col-span-1 bg-white dark:bg-graphite-800 rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-4">Складские помещения</h2>
          {loading ? (
            <div className="text-gray-500 text-center py-4">Загрузка...</div>
          ) : (
            <div className="space-y-2">
              {rooms.map(room => (
                <button
                  key={room.id}
                  onClick={() => setSelectedRoom(room.id)}
                  className={`w-full text-left px-3 py-2 rounded transition ${
                    selectedRoom === room.id
                      ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                      : 'hover:bg-gray-100 dark:hover:bg-graphite-700'
                  }`}
                >
                  <div className="font-medium">{room.name}</div>
                  <div className="text-xs text-gray-500">{room.department_name}</div>
                </button>
              ))}
              {rooms.length === 0 && (
                <div className="text-gray-500 text-center py-4">Нет складов</div>
              )}
            </div>
          )}
        </div>

        {/* Локации выбранного склада */}
        <div className="md:col-span-2 bg-white dark:bg-graphite-800 rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-4">
            {selectedRoom ? rooms.find(r => r.id === selectedRoom)?.name : 'Выберите склад'}
          </h2>
          {loading ? (
            <div className="text-gray-500 text-center py-4">Загрузка...</div>
          ) : selectedRoom ? (
            <div className="space-y-2">
              {locations.map(loc => (
                <div
                  key={loc.id}
                  className="flex items-center justify-between px-3 py-2 rounded hover:bg-gray-50 dark:hover:bg-graphite-700"
                >
                  <div>
                    <div className="font-medium">{loc.name}</div>
                    <div className="text-xs text-gray-500">
                      {loc.code && `Код: ${loc.code} • `}
                      Тип: {loc.location_type}
                    </div>
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {loc.current_count} объектов
                  </div>
                </div>
              ))}
              {locations.length === 0 && (
                <div className="text-gray-500 text-center py-4">Нет локаций</div>
              )}
            </div>
          ) : (
            <div className="text-gray-500 text-center py-8">
              Выберите склад слева для просмотра локаций
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Warehouse;
