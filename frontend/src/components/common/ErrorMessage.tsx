// frontend/src/components/common/ErrorMessage.tsx
import React from 'react';
import { AlertCircle, XCircle, Info, CheckCircle2 } from 'lucide-react';

type MessageType = 'error' | 'warning' | 'info' | 'success';

interface MessageProps {
  message: string;
  type?: MessageType;
  onClose?: () => void;
  className?: string;
}

const ErrorMessage: React.FC<MessageProps> = ({
  message,
  type = 'error',
  onClose,
  className = '',
}) => {
  const styles: Record<MessageType, { bg: string; border: string; text: string; icon: React.ComponentType<{ className?: string }> }> = {
    error: {
      bg: 'bg-red-50 dark:bg-red-900/20',
      border: 'border-red-200 dark:border-red-800',
      text: 'text-red-800 dark:text-red-200',
      icon: AlertCircle,
    },
    warning: {
      bg: 'bg-yellow-50 dark:bg-yellow-900/20',
      border: 'border-yellow-200 dark:border-yellow-800',
      text: 'text-yellow-800 dark:text-yellow-200',
      icon: AlertCircle,
    },
    info: {
      bg: 'bg-blue-50 dark:bg-blue-900/20',
      border: 'border-blue-200 dark:border-blue-800',
      text: 'text-blue-800 dark:text-blue-200',
      icon: Info,
    },
    success: {
      bg: 'bg-green-50 dark:bg-green-900/20',
      border: 'border-green-200 dark:border-green-800',
      text: 'text-green-800 dark:text-green-200',
      icon: CheckCircle2,
    },
  };

  const config = styles[type];
  const Icon = config.icon;

  return (
    <div className={`rounded-lg border ${config.bg} ${config.border} ${config.text} px-4 py-3 flex items-start gap-3 ${className}`}>
      <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
      <p className="text-sm flex-1">{message}</p>
      {onClose && (
        <button
          onClick={onClose}
          className="flex-shrink-0 p-1 rounded hover:bg-black/10 dark:hover:bg-white/10 transition"
        >
          <XCircle className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};

export { ErrorMessage };
export default ErrorMessage;
