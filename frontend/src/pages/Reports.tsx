// frontend/src/pages/Reports.tsx
import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { 
  FileText, Download, BarChart3, PieChart, TrendingDown, 
  Package, Wrench, Users, Building2, AlertTriangle, 
  Upload, FileSpreadsheet, RefreshCw, ChevronDown, ChevronUp,
  ExternalLink
} from 'lucide-react';
import toast from 'react-hot-toast';

// ====================== ВСПОМОГАТЕЛЬНЫЕ ======================

const formatMoney = (value: number) => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

const formatPercent = (value: number) => {
  return `${value.toFixed(1)}%`;
};

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    active: 'bg-green-500',
    maintenance: 'bg-yellow-500',
    reserved: 'bg-blue-500',
    decommissioned: 'bg-gray-500',
    lost: 'bg-red-500',
    written_off: 'bg-red-700',
  };
  return colors[status] || 'bg-gray-400';
};

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    active: 'Активен',
    maintenance: 'На ремонте',
    reserved: 'В резерве',
    decommissioned: 'Выведен',
    lost: 'Утерян',
    written_off: 'Списан',
  };
  return labels[status] || status;
};

// ====================== КОМПОНЕНТЫ ДИАГРАММ ======================

interface BarChartProps {
  data: Array<{ label: string; value: number; color?: string; icon?: string; maxValue?: number }>;
  valueLabel?: string;
  showPercent?: boolean;
}

const HorizontalBarChart: React.FC<BarChartProps> = ({ data, valueLabel, showPercent = true }) => {
  const maxValue = Math.max(...data.map(d => d.value), 1);
  const total = data.reduce((s, d) => s + d.value, 0);

  return (
    <div className="space-y-2">
      {data.map((item, i) => (
        <div key={i}>
          <div className="flex justify-between text-xs mb-0.5">
            <span className="text-gray-700 dark:text-gray-300 truncate flex items-center gap-1">
              {item.icon && <span>{item.icon}</span>}
              {item.label}
            </span>
            <span className="text-gray-500 dark:text-gray-400 font-medium">
              {item.value}
              {showPercent && total > 0 && (
                <span className="text-gray-400 ml-1">({(item.value / total * 100).toFixed(1)}%)</span>
              )}
            </span>
          </div>
          <div className="w-full bg-gray-100 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${(item.value / maxValue) * 100}%`,
                backgroundColor: item.color || '#3B82F6',
                minWidth: item.value > 0 ? '12px' : '0px',
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color: string;
  trend?: 'up' | 'down' | 'neutral';
}

const StatCard: React.FC<StatCardProps> = ({ title, value, subtitle, icon, color, trend }) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider truncate">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{subtitle}</p>
          )}
        </div>
        <div className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
          {icon}
        </div>
      </div>
    </div>
  );
};

// ====================== ОСНОВНОЙ КОМПОНЕНТ ======================

interface ReportConfig {
  id: string;
  name: string;
  description: string;
  icon: string;
  formats: string[];
  longDescription: string;
}

const REPORTS: ReportConfig[] = [
  {
    id: 'asset',
    name: 'Отчет по активам',
    description: 'Сводная информация по всем активам',
    icon: '📊',
    formats: ['excel', 'json'],
    longDescription: 'Общее количество, стоимость, распределение по типам, статусам и подразделениям.',
  },
  {
    id: 'depreciation',
    name: 'Отчет по амортизации',
    description: 'Анализ износа активов',
    icon: '📉',
    formats: ['excel', 'json'],
    longDescription: 'Уровень износа, активы с высоким износом, распределение по типам.',
  },
  {
    id: 'inventory',
    name: 'Отчет по инвентаризации',
    description: 'Полная статистика по имуществу',
    icon: '📋',
    formats: ['excel', 'json'],
    longDescription: 'Общая стоимость, количество, распределение по типам, статусам, подразделениям и помещениям.',
  },
  {
    id: 'import',
    name: 'Отчет об импорте',
    description: 'История и статистика импорта данных',
    icon: '📥',
    formats: ['excel', 'json'],
    longDescription: 'Статистика по импортированным файлам, успешность, количество обработанных строк.',
  },
];

const Reports: React.FC = () => {
  const [activeReport, setActiveReport] = useState<string | null>(null);
  const [reportData, setReportData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [loadingExport, setLoadingExport] = useState<string | null>(null);
  const [selectedFormats, setSelectedFormats] = useState<Record<string, string>>({});

  const fetchReport = useCallback(async (reportId: string) => {
    setLoading(true);
    setActiveReport(reportId);
    setReportData(null);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/reports/${reportId}-report`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setReportData(data);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Ошибка загрузки отчета');
        setActiveReport(null);
      }
    } catch {
      toast.error('Ошибка соединения');
      setActiveReport(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleExport = async (reportId: string) => {
    const format = selectedFormats[reportId] || 'excel';
    setLoadingExport(reportId);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/reports/${reportId}-report/export?format=${format}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      });

      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `report_${reportId}_${new Date().toISOString().slice(0, 10)}.${format === 'excel' ? 'xlsx' : 'json'}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        toast.success('Отчет скачан');
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Ошибка скачивания');
      }
    } catch {
      toast.error('Ошибка соединения');
    } finally {
      setLoadingExport(null);
    }
  };

  // ====================== РЕНДЕР ОТЧЕТОВ ======================

  const renderAssetReport = (data: any) => {
    const s = data.summary;
    const chartColors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'];

    return (
      <div className="space-y-6">
        {/* Summary cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard title="Всего активов" value={s.total_count} icon={<Package className="w-5 h-5 text-white" />} color="bg-blue-600" />
          <StatCard title="Текущая стоимость" value={formatMoney(s.total_current_value)} icon={<BarChart3 className="w-5 h-5 text-white" />} color="bg-green-600" />
          <StatCard title="Средний износ" value={formatPercent(s.depreciation_percent)} icon={<TrendingDown className="w-5 h-5 text-white" />} color="bg-orange-600" />
          <StatCard title="Требуют ремонта" value={s.needs_repair_count} subtitle={`${s.low_value_count} сильно устарели`} icon={<Wrench className="w-5 h-5 text-white" />} color="bg-red-600" />
        </div>

        {/* By type */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <PieChart className="w-4 h-4 text-blue-500" />
              По типам активов
            </h4>
            {data.type_breakdown?.length > 0 ? (
              <HorizontalBarChart
                data={data.type_breakdown.map((t: any, i: number) => ({
                  label: `${t.icon} ${t.name}`,
                  value: t.count,
                  color: chartColors[i % chartColors.length],
                  icon: t.icon,
                }))}
                valueLabel="шт."
              />
            ) : <p className="text-sm text-gray-400">Нет данных</p>}
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-green-500" />
              По статусам
            </h4>
            {data.status_breakdown?.length > 0 ? (
              <HorizontalBarChart
                data={data.status_breakdown.map((st: any) => ({
                  label: st.label,
                  value: st.count,
                  color: st.status === 'active' ? '#10B981' : st.status === 'maintenance' ? '#F59E0B' : st.status === 'reserved' ? '#3B82F6' : st.status === 'decommissioned' ? '#6B7280' : st.status === 'lost' ? '#EF4444' : '#9CA3AF',
                }))}
              />
            ) : <p className="text-sm text-gray-400">Нет данных</p>}
          </div>
        </div>

        {/* By department */}
        {data.department_breakdown?.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Building2 className="w-4 h-4 text-purple-500" />
              По подразделениям
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-2 px-3 text-gray-500 font-medium">Подразделение</th>
                    <th className="text-right py-2 px-3 text-gray-500 font-medium">Кол-во</th>
                    <th className="text-right py-2 px-3 text-gray-500 font-medium">Стоимость покупки</th>
                    <th className="text-right py-2 px-3 text-gray-500 font-medium">Текущая стоимость</th>
                    <th className="text-right py-2 px-3 text-gray-500 font-medium">Доля</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {data.department_breakdown.map((d: any, i: number) => (
                    <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="py-2 px-3 text-gray-900 dark:text-gray-100">{d.department}</td>
                      <td className="py-2 px-3 text-right text-gray-700 dark:text-gray-300">{d.count}</td>
                      <td className="py-2 px-3 text-right text-gray-700 dark:text-gray-300">{formatMoney(d.total_purchase)}</td>
                      <td className="py-2 px-3 text-right text-gray-700 dark:text-gray-300">{formatMoney(d.total_current)}</td>
                      <td className="py-2 px-3 text-right text-gray-500">{(d.count / s.total_count * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderDepreciationReport = (data: any) => {
    const s = data.summary;
    const wearColors = ['#EF4444', '#F59E0B', '#3B82F6', '#9CA3AF'];

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard title="Всего активов" value={s.total_assets} icon={<Package className="w-5 h-5 text-white" />} color="bg-blue-600" />
          <StatCard title="Первоначальная стоимость" value={formatMoney(s.total_purchase_value)} icon={<BarChart3 className="w-5 h-5 text-white" />} color="bg-green-600" />
          <StatCard title="Текущая стоимость" value={formatMoney(s.total_current_value)} icon={<TrendingDown className="w-5 h-5 text-white" />} color="bg-orange-600" />
          <StatCard title="Средний износ" value={formatPercent(s.avg_depreciation_percent)} subtitle={`Всего амортизации: ${formatMoney(s.total_depreciation)}`} icon={<TrendingDown className="w-5 h-5 text-white" />} color="bg-red-600" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <PieChart className="w-4 h-4 text-orange-500" />
              Уровень износа
            </h4>
            {data.wear_levels?.length > 0 ? (
              <HorizontalBarChart
                data={data.wear_levels.map((wl: any, i: number) => ({
                  label: wl.label,
                  value: wl.count,
                  color: wearColors[i],
                }))}
              />
            ) : <p className="text-sm text-gray-400">Нет данных</p>}
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-blue-500" />
              Износ по типам
            </h4>
            {data.type_wear?.length > 0 ? (
              <HorizontalBarChart
                data={data.type_wear.map((tw: any) => ({
                  label: `${tw.icon} ${tw.name}`,
                  value: tw.depreciation_percent,
                  icon: tw.icon,
                }))}
                valueLabel="%"
                showPercent={false}
              />
            ) : <p className="text-sm text-gray-400">Нет данных</p>}
          </div>
        </div>

        {/* High wear assets */}
        {data.high_wear_assets?.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                Активы с высоким износом ({data.high_wear_assets.length})
              </h4>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-2 px-3 text-gray-500 font-medium">Инв. номер</th>
                    <th className="text-left py-2 px-3 text-gray-500 font-medium">Название</th>
                    <th className="text-left py-2 px-3 text-gray-500 font-medium">Тип</th>
                    <th className="text-right py-2 px-3 text-gray-500 font-medium">Цена</th>
                    <th className="text-right py-2 px-3 text-gray-500 font-medium">Остаток</th>
                    <th className="text-right py-2 px-3 text-gray-500 font-medium">Износ</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {data.high_wear_assets.map((a: any) => (
                    <tr key={a.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="py-2 px-3 font-mono text-gray-900 dark:text-gray-100">{a.inventory_number}</td>
                      <td className="py-2 px-3 text-gray-900 dark:text-gray-100">{a.name}</td>
                      <td className="py-2 px-3 text-gray-600 dark:text-gray-400">{a.type}</td>
                      <td className="py-2 px-3 text-right text-gray-700 dark:text-gray-300">{formatMoney(a.purchase_price)}</td>
                      <td className="py-2 px-3 text-right text-gray-700 dark:text-gray-300">{formatMoney(a.current_value)}</td>
                      <td className="py-2 px-3 text-right">
                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300">
                          {a.wear_percent}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderInventoryReport = (data: any) => {
    const s = data.summary;
    const chartColors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6'];

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard title="Всего активов" value={s.total_count} icon={<Package className="w-5 h-5 text-white" />} color="bg-blue-600" />
          <StatCard title="Текущая стоимость" value={formatMoney(s.total_current_value)} icon={<BarChart3 className="w-5 h-5 text-white" />} color="bg-green-600" />
          <StatCard title="Средняя стоимость" value={formatMoney(s.avg_value_per_asset)} subtitle="на один актив" icon={<BarChart3 className="w-5 h-5 text-white" />} color="bg-purple-600" />
          <StatCard title="Требуют ремонта" value={s.needs_repair_count} subtitle={`${s.no_responsible_count} без ответственного`} icon={<Wrench className="w-5 h-5 text-white" />} color="bg-red-600" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <PieChart className="w-4 h-4 text-blue-500" />
              По типам активов
            </h4>
            {data.type_breakdown?.length > 0 ? (
              <HorizontalBarChart
                data={data.type_breakdown.map((t: any, i: number) => ({
                  label: `${t.icon} ${t.name}`,
                  value: t.count,
                  color: chartColors[i % chartColors.length],
                  icon: t.icon,
                }))}
              />
            ) : <p className="text-sm text-gray-400">Нет данных</p>}
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-green-500" />
              По статусам
            </h4>
            {data.status_breakdown?.length > 0 ? (
              <HorizontalBarChart
                data={data.status_breakdown.map((st: any) => ({
                  label: st.label,
                  value: st.count,
                  color: st.status === 'active' ? '#10B981' : st.status === 'maintenance' ? '#F59E0B' : st.status === 'reserved' ? '#3B82F6' : st.status === 'decommissioned' ? '#6B7280' : st.status === 'lost' ? '#EF4444' : '#9CA3AF',
                }))}
              />
            ) : <p className="text-sm text-gray-400">Нет данных</p>}
          </div>
        </div>

        {/* By department */}
        {data.department_breakdown?.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Building2 className="w-4 h-4 text-purple-500" />
              По подразделениям
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-2 px-3 text-gray-500 font-medium">Подразделение</th>
                    <th className="text-right py-2 px-3 text-gray-500 font-medium">Кол-во</th>
                    <th className="text-right py-2 px-3 text-gray-500 font-medium">Стоимость</th>
                    <th className="text-right py-2 px-3 text-gray-500 font-medium">Доля</th>
                    <th className="text-left py-2 px-3 text-gray-500 font-medium">Ответственные</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {data.department_breakdown.map((d: any, i: number) => (
                    <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="py-2 px-3 text-gray-900 dark:text-gray-100">{d.department_name}</td>
                      <td className="py-2 px-3 text-right text-gray-700 dark:text-gray-300">{d.count}</td>
                      <td className="py-2 px-3 text-right text-gray-700 dark:text-gray-300">{formatMoney(d.total_current)}</td>
                      <td className="py-2 px-3 text-right text-gray-500">{(d.count / s.total_count * 100).toFixed(1)}%</td>
                      <td className="py-2 px-3 text-gray-600 dark:text-gray-400 truncate max-w-[200px]">
                        {d.responsible_persons?.join(', ') || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* By location */}
        {data.location_breakdown?.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Building2 className="w-4 h-4 text-cyan-500" />
              По помещениям (топ-20)
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-2 px-3 text-gray-500 font-medium">Помещение</th>
                    <th className="text-right py-2 px-3 text-gray-500 font-medium">Кол-во</th>
                    <th className="text-right py-2 px-3 text-gray-500 font-medium">Стоимость</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {data.location_breakdown.map((l: any, i: number) => (
                    <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="py-2 px-3 text-gray-900 dark:text-gray-100">{l.location}</td>
                      <td className="py-2 px-3 text-right text-gray-700 dark:text-gray-300">{l.count}</td>
                      <td className="py-2 px-3 text-right text-gray-700 dark:text-gray-300">{formatMoney(l.total_current)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderImportReport = (data: any) => {
    const s = data.summary;

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard title="Всего импортов" value={s.total_imports} icon={<Upload className="w-5 h-5 text-white" />} color="bg-blue-600" />
          <StatCard title="Успешных" value={s.successful_imports} subtitle={`${s.success_rate}% успешность`} icon={<FileSpreadsheet className="w-5 h-5 text-white" />} color="bg-green-600" />
          <StatCard title="С ошибками" value={s.failed_imports} icon={<AlertTriangle className="w-5 h-5 text-white" />} color="bg-red-600" />
          <StatCard title="Импортировано строк" value={s.total_rows_imported} subtitle={`${s.total_rows_failed} с ошибками`} icon={<BarChart3 className="w-5 h-5 text-white" />} color="bg-purple-600" />
        </div>

        {/* Type stats */}
        {data.type_stats?.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <PieChart className="w-4 h-4 text-blue-500" />
              По типам импорта
            </h4>
            <HorizontalBarChart
              data={data.type_stats.map((ts: any, i: number) => ({
                label: ts.type,
                value: ts.count,
                color: ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6'][i],
              }))}
            />
          </div>
        )}

        {/* Recent jobs */}
        {data.recent_jobs?.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <RefreshCw className="w-4 h-4 text-gray-500" />
              Последние импорты
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-2 px-3 text-gray-500 font-medium">Файл</th>
                    <th className="text-left py-2 px-3 text-gray-500 font-medium">Тип</th>
                    <th className="text-left py-2 px-3 text-gray-500 font-medium">Статус</th>
                    <th className="text-right py-2 px-3 text-gray-500 font-medium">Строк</th>
                    <th className="text-right py-2 px-3 text-gray-500 font-medium">Успешно</th>
                    <th className="text-right py-2 px-3 text-gray-500 font-medium">Ошибок</th>
                    <th className="text-right py-2 px-3 text-gray-500 font-medium">Дата</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {data.recent_jobs.map((job: any, i: number) => {
                    const statusColors: Record<string, string> = {
                      completed: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
                      failed: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
                      processing: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
                      pending: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
                    };
                    const statusLabels: Record<string, string> = {
                      completed: 'Завершён',
                      failed: 'Ошибка',
                      processing: 'Выполняется',
                      pending: 'Ожидает',
                    };
                    return (
                      <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                        <td className="py-2 px-3 text-gray-900 dark:text-gray-100 font-medium truncate max-w-[200px]">{job.filename}</td>
                        <td className="py-2 px-3 text-gray-600 dark:text-gray-400">{job.import_type}</td>
                        <td className="py-2 px-3">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[job.status] || 'bg-gray-100 text-gray-700'}`}>
                            {statusLabels[job.status] || job.status}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-right text-gray-700 dark:text-gray-300">{job.total_rows}</td>
                        <td className="py-2 px-3 text-right text-green-600 dark:text-green-400">{job.successful_rows}</td>
                        <td className="py-2 px-3 text-right">
                          {job.failed_rows > 0 ? (
                            <span className="text-red-600 dark:text-red-400">{job.failed_rows}</span>
                          ) : (
                            <span className="text-gray-400">0</span>
                          )}
                        </td>
                        <td className="py-2 px-3 text-right text-gray-500">
                          {job.created_at ? new Date(job.created_at).toLocaleDateString('ru-RU') : '—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  };

  // ====================== РЕНДЕР ======================

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <BarChart3 className="w-7 h-7 text-blue-600" />
            Отчеты и аналитика
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Статистика и анализ текущего состояния имущества
          </p>
        </div>
        <Link
          to="/dashboard"
          className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 font-medium text-sm"
        >
          ← Назад на дашборд
        </Link>
      </div>

      {/* Report Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {REPORTS.map((report) => (
          <div
            key={report.id}
            className={`bg-white dark:bg-gray-800 rounded-xl border-2 transition-all cursor-pointer ${
              activeReport === report.id
                ? 'border-blue-500 dark:border-blue-400 shadow-lg'
                : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600 hover:shadow-md'
            }`}
            onClick={() => fetchReport(report.id)}
          >
            <div className="p-5">
              <div className="flex items-start justify-between mb-3">
                <div className="text-3xl">{report.icon}</div>
                <div className="flex gap-2">
                  {report.formats.map((fmt) => (
                    <span
                      key={fmt}
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        fmt === 'excel' ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' : 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                      }`}
                    >
                      {fmt.toUpperCase()}
                    </span>
                  ))}
                </div>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">{report.name}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">{report.description}</p>
              <p className="text-xs text-gray-400 dark:text-gray-500">{report.longDescription}</p>
            </div>
            <div className="px-5 pb-4 flex gap-2">
              <button
                onClick={(e) => { e.stopPropagation(); handleExport(report.id); }}
                disabled={loadingExport === report.id}
                className="flex-1 px-3 py-2 text-xs border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition disabled:opacity-50 flex items-center justify-center gap-1.5"
              >
                {loadingExport === report.id ? (
                  <>⏳ Загрузка...</>
                ) : (
                  <><Download className="w-3.5 h-3.5" /> Скачать</>
                )}
              </button>
              <button
                onClick={() => fetchReport(report.id)}
                className="flex-1 px-3 py-2 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center justify-center gap-1.5"
              >
                <BarChart3 className="w-3.5 h-3.5" />
                Просмотр
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Report Content */}
      {loading && (
        <div className="flex justify-center items-center py-16">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
          <span className="ml-3 text-gray-500 dark:text-gray-400">Загрузка отчета...</span>
        </div>
      )}

      {!loading && activeReport && reportData && (
        <div className="bg-gray-50 dark:bg-gray-900/50 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                {REPORTS.find(r => r.id === activeReport)?.icon} {reportData.title}
              </h2>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                Сгенерирован: {new Date(reportData.generated_at).toLocaleString('ru-RU')}
              </p>
            </div>
            <button
              onClick={() => handleExport(activeReport)}
              disabled={loadingExport === activeReport}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              {loadingExport === activeReport ? 'Загрузка...' : 'Скачать отчет'}
            </button>
          </div>

          {activeReport === 'asset' && renderAssetReport(reportData)}
          {activeReport === 'depreciation' && renderDepreciationReport(reportData)}
          {activeReport === 'inventory' && renderInventoryReport(reportData)}
          {activeReport === 'import' && renderImportReport(reportData)}
        </div>
      )}

      {!loading && !activeReport && (
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-6 text-center">
          <BarChart3 className="w-12 h-12 text-blue-400 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-200 mb-2">Выберите отчёт</h3>
          <p className="text-blue-700 dark:text-blue-300 text-sm">
            Нажмите на карточку отчёта, чтобы увидеть детальную статистику с графиками и таблицами.
            Также можно скачать отчёт в формате Excel или JSON.
          </p>
        </div>
      )}
    </div>
  );
};

export default Reports;