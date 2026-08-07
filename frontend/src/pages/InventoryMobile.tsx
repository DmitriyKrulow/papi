// frontend/src/pages/InventoryMobile.tsx
import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { CheckCircle2, XCircle, Loader2, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

interface Asset {
  id: number;
  inventory_number: string;
  name: string;
  model?: string;
  location?: string;
  responsible?: string;
  last_inventory_date?: string;
  last_inventory_confirmed?: boolean;
}

interface InventoryCheck {
  id: number;
  name: string;
  check_type: string;
  started_at: string;
  found: number;
  missing: number;
  total_checked: number;
}

const InventoryMobile: React.FC = () => {
  const navigate = useNavigate();
  const { user, getToken } = useAuth();
  const [activeInventory, setActiveInventory] = useState<InventoryCheck | null>(null);
  const [myAssets, setMyAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      
      // Получаем активную инвентаризацию
      const invRes = await fetch('/api/inventory-checks/active', {
        headers: { 'Authorization': token ? `Bearer ${token}` : '' },
      });
      
      let invData = null;
      if (invRes.ok) {
        invData = await invRes.json();
        setActiveInventory(invData);
      }
      
      // Получаем активы пользователя только если есть инвентаризация
      if (invData) {
        const assetsRes = await fetch('/api/inventory-checks/my-assets', {
          headers: { 'Authorization': token ? `Bearer ${token}` : '' },
        });
        
        if (assetsRes.ok) {
          const assetsData = await assetsRes.json();
          setMyAssets(assetsData);
        }
      }
    } catch (err) {
      toast.error('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const pendingAssets = myAssets.filter(a => !a.last_inventory_confirmed);
  const confirmedAssets = myAssets.filter(a => a.last_inventory_confirmed);
  const progress = myAssets.length > 0 
    ? Math.round((confirmedAssets.length / myAssets.length) * 100) 
    : 0;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-blue-600 dark:text-blue-400 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">Загрузка...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 pb-20">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between p-4">
          <button
            onClick={() => navigate('/inventory')}
            className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="font-medium">Назад</span>
          </button>
          <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">
            Инвентаризация
          </h1>
          <div className="w-20"></div>
        </div>
      </div>

      {/* Progress */}
      {activeInventory && myAssets.length > 0 && (
        <div className="p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Общий прогресс
              </span>
              <span className="text-sm font-bold text-blue-600 dark:text-blue-400">
                {progress}%
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
              <div
                className="bg-blue-600 dark:bg-blue-500 h-3 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-2">
              <span>Проверено: {confirmedAssets.length}/{myAssets.length}</span>
              <span>Осталось: {pendingAssets.length}</span>
            </div>
          </div>
        </div>
      )}

      {/* My Assets */}
      <div className="p-4">
        <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-3">
          Моё имущество
        </h2>

        {myAssets.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center border border-gray-200 dark:border-gray-700">
            <p className="text-gray-500 dark:text-gray-400">У вас нет назначенного имущества</p>
          </div>
        ) : (
          <div className="space-y-3">
            {myAssets.map((asset) => (
              <div
                key={asset.id}
                className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 border ${
                  asset.last_inventory_confirmed
                    ? 'border-green-200 dark:border-green-800'
                    : 'border-gray-200 dark:border-gray-700'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900 dark:text-gray-100">
                      {asset.name}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 font-mono mt-1">
                      Инв. №: {asset.inventory_number}
                    </p>
                    {asset.model && (
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                        Модель: {asset.model}
                      </p>
                    )}
                    {asset.location && (
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                        📍 {asset.location}
                      </p>
                    )}
                  </div>
                  <div className="ml-3">
                    {asset.last_inventory_confirmed ? (
                      <CheckCircle2 className="w-6 h-6 text-green-600 dark:text-green-400" />
                    ) : (
                      <XCircle className="w-6 h-6 text-gray-300 dark:text-gray-600" />
                    )}
                  </div>
                </div>
                
                {/* Click to view details */}
                {!asset.last_inventory_confirmed && activeInventory && (
                  <button
                    onClick={() => navigate(`/inventory/asset/${asset.id}?check_id=${activeInventory.id}`)}
                    className="mt-3 w-full px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg text-sm hover:bg-blue-700 dark:hover:bg-blue-600 transition font-medium"
                  >
                    Проверить актив
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* No Active Inventory */}
      {!activeInventory && (
        <div className="p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center border border-gray-200 dark:border-gray-700">
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              Нет активных инвентаризаций
            </p>
            <button
              onClick={() => navigate('/assets')}
              className="px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 transition"
            >
              Перейти к активам
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default InventoryMobile;
