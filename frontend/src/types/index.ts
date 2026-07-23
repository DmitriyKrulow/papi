// frontend/src/types/index.ts

// ========== Активы ==========
export interface Asset {
  id: number;
  inventory_number: string;
  name: string;
  description?: string;
  model?: string;
  asset_type?: string;
  status: 'active' | 'maintenance' | 'reserved' | 'decommissioned' | 'lost' | 'written_off';
  purchase_price?: number;
  current_value?: number;
  department_code?: string;
  responsible_person?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ========== Пользователи ==========
export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  phone?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ========== Заявки на ремонт ==========
export interface RepairRequest {
  id: number;
  asset_id: number;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'draft' | 'submitted' | 'approved' | 'in_progress' | 'completed' | 'rejected' | 'cancelled';
  created_by: number;
  created_at: string;
  assigned_to?: number;
  estimated_cost?: number;
  actual_cost?: number;
}

// ========== Общие типы ==========
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, any>;
}

// ========== Статусы ==========
export const AssetStatusMap = {
  active: { label: 'Активен', color: 'green' },
  maintenance: { label: 'На ремонте', color: 'yellow' },
  reserved: { label: 'В резерве', color: 'blue' },
  decommissioned: { label: 'Выведен', color: 'gray' },
  lost: { label: 'Утерян', color: 'red' },
  written_off: { label: 'Списан', color: 'red' },
} as const;

export const RepairStatusMap = {
  draft: { label: 'Черновик', color: 'gray' },
  submitted: { label: 'Подана', color: 'blue' },
  approved: { label: 'Одобрена', color: 'green' },
  in_progress: { label: 'В работе', color: 'yellow' },
  completed: { label: 'Выполнена', color: 'green' },
  rejected: { label: 'Отклонена', color: 'red' },
  cancelled: { label: 'Отменена', color: 'gray' },
} as const;

export const PriorityMap = {
  low: { label: 'Низкий', color: 'gray' },
  medium: { label: 'Средний', color: 'blue' },
  high: { label: 'Высокий', color: 'orange' },
  urgent: { label: 'Срочный', color: 'red' },
} as const;