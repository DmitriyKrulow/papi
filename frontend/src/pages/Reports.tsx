// frontend/src/pages/Reports.tsx
import { useState } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';

interface Report {
  id: string;
  name: string;
  description: string;
  parameters: string[];
  formats: string[];
  icon: string;
}

const Reports: React.FC = () => {
  const [loadingReport, setLoadingReport] = useState<string | null>(null);
  const [selectedFormat, setSelectedFormat] = useState<Record<string, string>>({});

  const reports: Report[] = [
    {
      id: 'asset',
      name: 'Отчет по активам',
      description: 'Сводная информация по всем активам',
      parameters: ['include_photos', 'include_history'],
      formats: ['excel', 'pdf', 'json'],
      icon: '📊',
    },
    {
      id: 'depreciation',
      name: 'Отчет по амортизации',
      description: 'Информация по амортизации активов',
      parameters: ['report_date'],
      formats: ['excel', 'pdf', 'json'],
      icon: '📉',
    },
    {
      id: 'inventory',
      name: 'Отчет по инвентаризации',
      description: 'Отчет по конкретной инвентаризации',
      parameters: ['check_id'],
      formats: ['excel', 'pdf', 'json'],
      icon: '📋',
    },
    {
      id: 'import',
      name: 'Отчет об импорте',
      description: 'Отчет о результатах импорта данных из файла',
      parameters: ['file_path'],
      formats: ['excel', 'json'],
      icon: '📥',
    },
  ];

  const getFileExtension = (format: string): string => {
    switch (format) {
      case 'excel':
        return 'xlsx';
      case 'pdf':
        return 'pdf';
      case 'json':
        return 'json';
      default:
        return 'json';
    }
  };

  const getFormatLabel = (format: string): string => {
    switch (format) {
      case 'excel':
        return 'Excel';
      case 'pdf':
        return 'PDF';
      case 'json':
        return 'JSON';
      default:
        return format;
    }
  };

  const getFormatColor = (format: string): string => {
    switch (format) {
      case 'excel':
        return 'bg-green-100 text-green-700';
      case 'pdf':
        return 'bg-red-100 text-red-700';
      case 'json':
        return 'bg-blue-100 text-blue-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const handleDownload = async (reportId: string) => {
    const format = selectedFormat[reportId] || 'excel';
    setLoadingReport(reportId);
    
    try {
      const token = localStorage.getItem('token');
      
      // Используем новый эндпоинт для экспорта с форматом
      const response = await fetch(`/api/reports/${reportId}-report/export?format=${format}`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });

      if (response.status === 401) {
        toast.error('Сессия истекла. Пожалуйста, войдите заново');
        window.location.href = '/login';
        return;
      }

      if (response.ok) {
        // Получаем файл как blob
        const blob = await response.blob();
        const blobUrl = URL.createObjectURL(blob);
        
        // Определяем имя файла
        const extension = getFileExtension(format);
        const filename = `report_${reportId}_${new Date().toISOString().slice(0,10)}.${extension}`;
        
        // Скачиваем файл
        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(blobUrl);
        
        toast.success(`Отчет "${reportId}" скачан в формате ${getFormatLabel(format).toUpperCase()}`);
      } else {
        let errorMessage = `Ошибка: ${response.status}`;
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            errorMessage = errorData.detail;
          } else if (errorData.message) {
            errorMessage = errorData.message;
          }
        } catch {
          const text = await response.text();
          if (text) {
            errorMessage = text;
          }
        }
        throw new Error(errorMessage);
      }
    } catch (err: any) {
      toast.error(`Ошибка загрузки отчета: ${err.message}`);
      console.error('Download error:', err);
    } finally {
      setLoadingReport(null);
    }
  };

  const handleFormatChange = (reportId: string, format: string) => {
    setSelectedFormat((prev) => ({
      ...prev,
      [reportId]: format,
    }));
  };

  return (
    <div>
      <div className="flex flex-wrap justify-between items-center gap-4 mb-6">
        <h1 className="text-2xl font-bold text-gray-800">📊 Отчеты</h1>
        <Link
          to="/assets"
          className="text-blue-600 hover:text-blue-800 font-medium"
        >
          ← Назад к активам
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {reports.map((report) => (
          <div
            key={report.id}
            className="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition card-hover"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="text-4xl">{report.icon}</div>
              <div className="flex gap-2 flex-wrap">
                {report.formats.map((format) => (
                  <span
                    key={format}
                    className={`px-2 py-1 rounded text-xs font-medium ${getFormatColor(format)}`}
                  >
                    {getFormatLabel(format).toUpperCase()}
                  </span>
                ))}
              </div>
            </div>

            <h3 className="text-lg font-semibold mb-2">{report.name}</h3>
            <p className="text-gray-600 text-sm mb-4">{report.description}</p>

            {report.parameters.length > 0 && (
              <div className="mb-4">
                <span className="text-xs font-medium text-gray-500 uppercase">
                  Параметры:
                </span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {report.parameters.map((param) => (
                    <span
                      key={param}
                      className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                    >
                      {param}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Выбор формата */}
            <div className="mb-4">
              <label className="text-sm font-medium text-gray-700">Формат:</label>
              <select
                value={selectedFormat[report.id] || 'excel'}
                onChange={(e) => handleFormatChange(report.id, e.target.value)}
                className="ml-2 px-3 py-1 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                disabled={loadingReport === report.id}
              >
                {report.formats.map((format) => (
                  <option key={format} value={format}>
                    {getFormatLabel(format)}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={() => handleDownload(report.id)}
              disabled={loadingReport === report.id}
              className={`w-full py-2 rounded-lg font-medium transition flex items-center justify-center gap-2 ${
                loadingReport === report.id
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {loadingReport === report.id ? (
                <>
                  <span className="animate-spin">⏳</span> Загрузка...
                </>
              ) : (
                <>
                  <span>⬇️</span> Скачать отчет
                </>
              )}
            </button>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-800 mb-2">ℹ️ Информация</h3>
        <p className="text-blue-700 text-sm">
          Отчеты доступны в форматах Excel (.xlsx), PDF и JSON. Выберите нужный формат перед скачиванием.
          Отчет об импорте доступен в форматах Excel и JSON.
        </p>
      </div>
    </div>
  );
};

export default Reports;