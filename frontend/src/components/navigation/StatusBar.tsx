// frontend/src/components/navigation/StatusBar.tsx
import { useState, useEffect } from 'react';
import { Wifi, WifiOff, AlertCircle } from 'lucide-react';

interface StatusBarProps {
  onToggleCompact?: (compact: boolean) => void;
  compactMode?: boolean;
}

const StatusBar = ({ onToggleCompact, compactMode = false }: StatusBarProps) => {
  const [dbStatus, setDbStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const [compactModeLocal, setCompactModeLocal] = useState(compactMode);

  useEffect(() => {
    const checkDb = async () => {
      try {
        const res = await fetch('/api/db-check');
        if (res.ok) {
          const data = await res.json();
          setDbStatus(data.status === 'connected' ? 'connected' : 'disconnected');
        } else {
          setDbStatus('disconnected');
        }
      } catch {
        setDbStatus('disconnected');
      }
    };
    checkDb();
    const interval = setInterval(checkDb, 30000);
    return () => clearInterval(interval);
  }, []);

  // Sync with parent
  useEffect(() => { setCompactModeLocal(compactMode); }, [compactMode]);

  const statusConfig = {
    checking: { icon: <span className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />, text: 'Проверка...', color: 'text-yellow-600 dark:text-yellow-400' },
    connected: { icon: <Wifi className="w-3.5 h-3.5" />, text: 'Подключено', color: 'text-green-600 dark:text-green-400' },
    disconnected: { icon: <WifiOff className="w-3.5 h-3.5" />, text: 'Нет данных', color: 'text-gray-500 dark:text-gray-400' },
  };

  const status = statusConfig[dbStatus];

  return (
    <header className="sticky top-0 z-20 bg-white/80 dark:bg-graphite-900/80 backdrop-blur-md border-b border-gray-100 dark:border-graphite-800">
      <div className="flex items-center justify-between px-4 py-2">
        {/* Left: connection status */}
        <div className={`flex items-center gap-2 text-xs ${status.color}`}>
          {status.icon}
          <span className="hidden sm:inline font-medium">{status.text}</span>
        </div>

        {/* Right: compact mode toggle */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              const newVal = !compactModeLocal;
              setCompactModeLocal(newVal);
              onToggleCompact?.(newVal);
            }}
            className={`px-2.5 py-1 text-[11px] rounded-full transition-all ${
              compactModeLocal
                ? 'bg-accent-400/20 text-accent-600 dark:text-accent-400 font-medium'
                : 'bg-gray-100 dark:bg-graphite-800 text-gray-500 dark:text-graphite-400 hover:bg-gray-200 dark:hover:bg-graphite-700'
            }`}
            title="Компактный режим"
          >
            <span className="flex items-center gap-1">
              {compactModeLocal ? (
                <>
                  <span className="w-3 h-3">▦</span> Компакт
                </>
              ) : (
                <>
                  <span className="w-3 h-3">▢</span> Стандарт
                </>
              )}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
};

export default StatusBar;
