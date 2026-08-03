// frontend/src/hooks/useConfirmation.ts
import { useState, useCallback } from 'react';

interface UseConfirmationReturn {
  confirm: (options: { title: string; message: string; confirmText?: string; confirmVariant?: 'primary' | 'danger' }) => Promise<boolean>;
}

/**
 * Хук для показа нативного confirm с логированием в toast
 * Используется как замена window.confirm() для критических действий
 */
export function useConfirmation(): UseConfirmationReturn {
  const [loading, setLoading] = useState(false);

  const confirm = useCallback(async (options: {
    title: string;
    message: string;
    confirmText?: string;
    confirmVariant?: 'primary' | 'danger';
  }): Promise<boolean> => {
    setLoading(true);
    try {
      return window.confirm(`${options.title}\n\n${options.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  return { confirm };
}

export default useConfirmation;
