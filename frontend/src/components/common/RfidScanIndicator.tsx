// frontend/src/components/common/RfidScanIndicator.tsx
import { useState, useEffect } from 'react';

interface RfidScanIndicatorProps {
  isScanning?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const RfidScanIndicator = ({ isScanning = false, size = 'md', className = '' }: RfidScanIndicatorProps) => {
  const [detected, setDetected] = useState(false);

  // Симуляция обнаружения метки при сканировании
  useEffect(() => {
    if (!isScanning) {
      setDetected(false);
      return;
    }
    const timer = setTimeout(() => setDetected(true), 300);
    return () => clearTimeout(timer);
  }, [isScanning]);

  const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-10 h-10',
    lg: 'w-14 h-14',
  };

  const iconSizeClasses = {
    sm: 'w-3 h-3',
    md: 'w-5 h-5',
    lg: 'w-7 h-7',
  };

  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      {/* Внешняя волна */}
      {isScanning && (
        <>
          <span className={`absolute inset-0 rounded-full bg-accent-400/20 ${sizeClasses[size]} animate-scan-wave`} />
          <span className={`absolute inset-0 rounded-full bg-accent-400/10 ${sizeClasses[size]} animate-scan-pulse`} />
        </>
      )}
      
      {/* Внутренний круг */}
      <div className={`
        relative z-10 flex items-center justify-center rounded-full
        ${sizeClasses[size]}
        ${isScanning
          ? 'bg-accent-400 text-white shadow-lg shadow-accent-400/40'
          : 'bg-gray-100 dark:bg-graphite-800 text-gray-400 dark:text-gray-500'
        }
        transition-all duration-300
      `}>
        <span className={iconSizeClasses[size]}>
          {isScanning ? '📡' : '📷'}
        </span>
      </div>
    </div>
  );
};

export default RfidScanIndicator;
