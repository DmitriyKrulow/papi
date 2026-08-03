// frontend/src/types/index.ts

// ========== Активы ==========
export interface AssetTypeConfig {
  code: string;
  name: string;
  icon: string;
  category: string;
  description: string;
  default_depreciation_years: number;
  default_maintenance_type?: string;
  maintenance_interval_months?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface MaintenanceEvent {
  id: number;
  asset_id: number;
  event_type: string;
  event_date: string;
  description?: string;
  cost?: number;
  performed_by?: string;
  next_event_date?: string;
  result?: string;
  document_number?: string;
  created_at: string;
}

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
  quantity?: number;
  department_code?: string;
  department_name?: string;
  responsible_person?: string;
  employee_name?: string;
  assigned_employee_id?: number;
  employee_id?: number;
  location_address?: string;
  manufacturer_code?: string;
  manufacturer_name?: string;
  purchase_date?: string;
  commissioning_date?: string;
  warranty_expiry?: string;
  serial_number?: string;
  capacity?: number;
  power?: string;
  weight?: string;
  consumable_type?: string;
  crypto_wallet_address?: string;
  crypto_token_symbol?: string;
  depreciation_years?: number;
  next_maintenance_date?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  // Поля инвентаризации
  last_inventory_date?: string;
  last_inventory_by_id?: number;
  last_inventory_confirmed?: boolean;
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

// ========== Подразделения (размещения) ==========
export interface Department {
  id: number;
  name: string;
  code: string;
  parent_id?: number;
  head?: string;
  phone?: string;
  email?: string;
  location?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface DepartmentOption {
  id: number;
  name: string;
  code: string;
  location: string;
  full_name: string;
}

export interface Room {
  id: number;
  department_id: number;
  name: string;
  floor?: string;
  building?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

// ========== Сотрудники ==========
export interface Employee {
  id: number;
  first_name: string;
  last_name: string;
  middle_name?: string;
  full_name: string;
  position?: string;
  position_code?: string;
  phone?: string;
  email?: string;
  employee_number?: string;
  department_id?: number;
  department_name?: string;
  department_code?: string;
  user_id?: number;
  username?: string;
  hire_date?: string;
  termination_date?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface EmployeeOption {
  id: number;
  full_name: string;
  position: string;
  department_name: string;
  department_code: string;
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

// ========== Типы активов ==========
export const AssetTypeNames: Record<string, { label: string; icon: string; color: string }> = {
  furniture: { label: 'Мебель', icon: '🪑', color: 'amber' },
  fire_extinguisher: { label: 'Огнетушители', icon: '🧯', color: 'red' },
  crypto_token: { label: 'Криптотокены', icon: '🔑', color: 'orange' },
  printer: { label: 'Принтеры', icon: '🖨️', color: 'blue' },
  computer: { label: 'Компьютеры', icon: '💻', color: 'gray' },
  consumables: { label: 'Расходники', icon: '📦', color: 'green' },
};

export const MaintenanceEventTypes: Record<string, { label: string; icon: string }> = {
  cleaning: { label: 'Чистка', icon: '🧹' },
  refilling: { label: 'Заправка', icon: '💧' },
  toner_replacement: { label: 'Замена тонера', icon: '🖨️' },
  repair: { label: 'Ремонт', icon: '🔧' },
  inspection: { label: 'Инвентаризация', icon: '📋' },
  warranty_check: { label: 'Гарантийное обслуживание', icon: '🛡️' },
  battery_replacement: { label: 'Замена батареи', icon: '🔋' },
  software_update: { label: 'Обновление ПО', icon: '💾' },
  calibration: { label: 'Калибровка', icon: '🎯' },
};