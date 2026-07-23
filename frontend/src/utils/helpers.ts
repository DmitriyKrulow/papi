// frontend/src/utils/helpers.ts

/**
 * Форматирование даты
 */
export const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * Форматирование денег
 */
export const formatMoney = (amount?: number): string => {
  if (!amount) return '0 ₽';
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
};

/**
 * Получение цвета статуса
 */
export const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    active: 'green',
    maintenance: 'yellow',
    reserved: 'blue',
    decommissioned: 'gray',
    lost: 'red',
    written_off: 'red',
    draft: 'gray',
    submitted: 'blue',
    approved: 'green',
    in_progress: 'yellow',
    completed: 'green',
    rejected: 'red',
    cancelled: 'gray',
    low: 'gray',
    medium: 'blue',
    high: 'orange',
    urgent: 'red',
  };
  return colors[status] || 'gray';
};

/**
 * Склеивание классов
 */
export const cn = (...classes: (string | undefined | null | false)[]): string => {
  return classes.filter(Boolean).join(' ');
};

/**
 * Генерация случайного ID (для тестов)
 */
export const generateId = (): string => {
  return Math.random().toString(36).substring(2, 9);
};