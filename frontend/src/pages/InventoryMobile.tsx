// frontend/src/pages/InventoryMobile.tsx
import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { CheckCircle2, XCircle, Loader2, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';

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
  const [searchParams] = useSearchParams();
  
  const forcedCheckId = searchParams.get('check_id') ? parseInt(searchParams.get('check_id') || '0') : null;
  
  const [activeInventory, setActiveInventory] = useState<InventoryCheck | null>(null);
  const [myAssets, setMyAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [forcedCheckId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      
      if (!token) {
        toast.error('Необходима авторизация');
        navigate('/login');
        return;
      }
      
      // Получаем активную инвентаризацию
      let invData: any = null;
      
      if (forcedCheckId && forcedCheckId > 0) {
        // Используем check_id из URL
        const invRes = await fetch(`/api/inventory-checks/${forcedCheckId}`, {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        
        if (invRes.ok) {
          const data = await invRes.json();
          if (data.status === 'in_progress') {
            invData = {
              id: data.id,
              name: data.name,
              check_type: data.check_type,
              started_at: data.started_at || '',
              found: data.found || 0,
              missing: data.missing || 0,
              total_checked: data.total_checked || 0,
            };
            setActiveInventory(invData);
          }
        }
      } else {
        // Получаем активную инвентаризацию
        const invRes = await fetch('/api/inventory-checks/active', {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        
        if (invRes.ok) {
          invData = await invRes.json();
          if (invData) {
            setActiveInventory(invData);
          }
        }
      }
      
      // Получаем активы пользователя только если есть инвентаризация
      if (invData) {
        const assetsRes = await fetch('/api/inventory-checks/my-assets', {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        
        if (assetsRes.ok) {
          const assetsData = await assetsRes.json();
          setMyAssets(assetsData);
        }
      }
    } catch (err) {
      console.error('Error fetching inventory data:', err);
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
    <div className="min-h-screen bg-gray-50 dark:bg-graphite-950 pb-20">
      {/* Header */}
      <div className="sticky top-0 z-20 bg-white/80 dark:bg-graphite-900/80 backdrop-blur-md border-b border-gray-100 dark:border-graphite-800">
        <div className="flex items-center justify-between p-3">
          <button
            onClick={() => navigate('/inventory')}
            className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400 hover:text-brand-600 dark:hover:text-accent-400 transition"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="font-medium text-sm">Назад</span>
          </button>
          <h1 className="text-base font-bold text-gray-900 dark:text-gray-100">
            Инвентаризация
          </h1>
          <div className="w-16"></div>
        </div>
      </div>

      {/* Progress */}
      {activeInventory && myAssets.length > 0 && (
        <div className="p-3">
          <div className="card-modern p-3">
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-xs font-medium text-gray-700 dark:text-gray-300 truncate max-w-[60%]">
                {activeInventory.name}
              </span>
              <span className="text-xs font-bold text-accent-600 dark:text-accent-400 ml-2">
                {progress}%
              </span>
            </div>
            <div className="progress-bar-modern">
              <div
                className="progress-bar-fill bg-accent-400"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-[10px] text-gray-500 dark:text-gray-400 mt-1.5">
              <span>Проверено: {confirmedAssets.length}/{myAssets.length}</span>
              <span>Осталось: {pendingAssets.length}</span>
            </div>
            <div className="flex justify-between text-[10px] mt-0.5">
              <span className="text-green-600 dark:text-green-400">✓ {activeInventory.found}</span>
              <span className="text-red-600 dark:text-red-400">✗ {activeInventory.missing}</span>
            </div>
          </div>
        </div>
      )}

      {/* My Assets */}
      <div className="p-3">
        <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">
          Моё имущество
        </h2>

        {myAssets.length === 0 ? (
          <div className="card-modern p-6 text-center">
            <p className="text-gray-500 dark:text-gray-400 text-sm">У вас нет назначенного имущества</p>
          </div>
        ) : (
          <div className="space-y-2">
            {myAssets.map((asset) => (
              <div
                key={asset.id}
                className={`card-modern p-3 ${
                  asset.last_inventory_confirmed
                    ? 'border-l-2 border-l-green-500'
                    : ''
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-sm text-gray-900 dark:text-gray-100 truncate">
                      {asset.name}
                    </h3>
                    <p className="text-[10px] text-gray-500 dark:text-gray-400 font-mono mt-0.5">
                      {asset.inventory_number}
                    </p>
                    {asset.model && (
                      <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">
                        {asset.model}
                      </p>
                    )}
                    {asset.location && (
                      <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">
                        📍 {asset.location}
                      </p>
                    )}
                  </div>
                  <div className="ml-2 flex-shrink-0">
                    {asset.last_inventory_confirmed ? (
                      <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />
                    ) : (
                      <XCircle className="w-5 h-5 text-gray-300 dark:text-gray-600" />
                    )}
                  </div>
                </div>
                
                {!asset.last_inventory_confirmed && activeInventory && (
                  <button
                    onClick={() => {
                      const checkId = forcedCheckId || activeInventory.id;
                      navigate(`/inventory/asset/${asset.id}?check_id=${checkId}`);
                    }}
                    className="mt-2 w-full px-3 py-1.5 bg-brand-500 dark:bg-brand-600 text-white rounded-card-sm text-xs hover:bg-brand-600 dark:hover:bg-brand-700 transition font-medium"
                  >
                    Проверить
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* No Active Inventory */}
      {!activeInventory && (
        <div className="p-3">
          <div className="card-modern p-6 text-center">
            <p className="text-gray-500 dark:text-gray-400 mb-3 text-sm">
              Нет активных инвентаризаций
            </p>
            <button
              onClick={() => navigate('/assets')}
              className="px-4 py-2 bg-brand-500 text-white rounded-card-sm hover:bg-brand-600 transition text-sm font-medium"
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
