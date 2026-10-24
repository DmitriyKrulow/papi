// frontend/src/components/navigation/navItems.tsx
import type { ReactNode } from 'react';
import {
  LayoutDashboard, Package, ClipboardList, Tag, BarChart3,
  FileText, Wrench, Calendar, Bell, Settings,
  Printer, TrendingUp, FileCheck, Scale, X,
} from 'lucide-react';

export interface NavItem {
  path: string;
  label: string;
  icon: ReactNode;
  adminOnly?: boolean;
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

export const useNavSections = (isAdmin: boolean): NavSection[] => [
  {
    title: 'Основное',
    items: [
      { path: '/dashboard', label: 'Дашборд', icon: <LayoutDashboard className="w-5 h-5" /> },
      { path: '/assets', label: 'Активы', icon: <Package className="w-5 h-5" /> },
      { path: '/inventory', label: 'Инвентаризация', icon: <ClipboardList className="w-5 h-5" /> },
      { path: '/marking', label: 'Маркировка', icon: <Tag className="w-5 h-5" /> },
      { path: '/reports', label: 'Отчёты', icon: <BarChart3 className="w-5 h-5" /> },
      { path: '/repairs', label: 'Ремонты', icon: <Wrench className="w-5 h-5" /> },
      { path: '/schedule', label: 'Расписание', icon: <Calendar className="w-5 h-5" /> },
      { path: '/notifications', label: 'Уведомления', icon: <Bell className="w-5 h-5" /> },
    ],
  },
  {
    title: 'Управление',
    items: isAdmin ? [
      { path: '/admin', label: 'Панель управления', icon: <Settings className="w-5 h-5" /> },
      { path: '/audit', label: 'Журнал аудита', icon: <FileText className="w-5 h-5" /> },
      { path: '/analytics', label: 'Аналитика', icon: <TrendingUp className="w-5 h-5" /> },
      { path: '/disposal', label: 'Списание', icon: <X className="w-5 h-5" /> },
      { path: '/regulatory', label: 'Документы', icon: <Scale className="w-5 h-5" /> },
      { path: '/reconciliation', label: 'Сверка', icon: <FileCheck className="w-5 h-5" /> },
      { path: '/room-inventory-print', label: 'Печать описи', icon: <Printer className="w-5 h-5" /> },
    ] : [],
  },
];
