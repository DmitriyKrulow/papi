// frontend/src/pages/RegulatoryPage.tsx
import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';

interface Doc {
  id: number;
  title: string;
  doc_type: string;
  document_number: string;
  document_date: string;
  applies_to_type: string;
  applies_to_id?: number;
  is_published: boolean;
  is_active: boolean;
  author_name?: string;
  created_at: string;
}

interface EquipmentStandard {
  id: number;
  position_code: string;
  position_name: string;
  asset_type_code: string;
  asset_type_name: string;
  quantity: number;
  priority: number;
}

const RegulatoryPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'documents' | 'standards' | 'responsibilities'>('documents');
  const [documents, setDocuments] = useState<Doc[]>([]);
  const [standards, setStandards] = useState<EquipmentStandard[]>([]);
  const [loading, setLoading] = useState(true);
  const [newDoc, setNewDoc] = useState({
    title: '', doc_type: 'equipment_standard', document_number: '',
    document_date: '', applies_to_type: '', applies_to_id: '',
    content: '', is_published: false,
  });

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const [docsRes, standardsRes] = await Promise.all([
        fetch('/api/regulatory/documents', { headers: { 'Authorization': `Bearer ${token}` } }),
        fetch('/api/regulatory/equipment-standards', { headers: { 'Authorization': `Bearer ${token}` } }),
      ]);
      if (docsRes.ok) {
        const data = await docsRes.json();
        setDocuments(data.documents || []);
      }
      if (standardsRes.ok) {
        const data = await standardsRes.json();
        setStandards(data.standards || []);
      }
    } catch (err) {
      console.error('Failed to fetch regulatory data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateDoc = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `/api/regulatory/documents?${new URLSearchParams({
          title: newDoc.title,
          doc_type: newDoc.doc_type,
          document_number: newDoc.document_number,
          document_date: newDoc.document_date,
          applies_to_type: newDoc.applies_to_type,
          applies_to_id: newDoc.applies_to_id || '',
          content: newDoc.content,
          is_published: String(newDoc.is_published),
        })}`,
        { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } },
      );
      if (response.ok) {
        toast.success('Документ создан');
        setNewDoc({ title: '', doc_type: 'equipment_standard', document_number: '', document_date: '', applies_to_type: '', applies_to_id: '', content: '', is_published: false });
        fetchData();
      }
    } catch (err) {
      toast.error('Ошибка создания');
    }
  };

  const docTypeLabels: Record<string, string> = {
    equipment_standard: '📋 Норматив оснащения',
    job_description: '📄 Должностная инструкция',
    responsibility: '⚖️ Ответственность',
    inventory_procedure: '📝 Порядок инвентаризации',
    disposal_procedure: '🗑️ Порядок списания',
  };

  if (loading) {
    return <div className="text-center py-8 text-gray-500">Загрузка...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Tabs */}
      <div className="flex gap-2">
        {(['documents', 'standards', 'responsibilities'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              activeTab === tab ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            {tab === 'documents' ? '📜 Документы' : tab === 'standards' ? '📋 Нормативы' : '⚖️ Ответственность'}
          </button>
        ))}
      </div>

      {/* Documents Tab */}
      {activeTab === 'documents' && (
        <div className="space-y-4">
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 border border-gray-100 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">Создать документ</h2>
            <div className="grid grid-cols-2 gap-3">
              <input
                type="text"
                placeholder="Название"
                value={newDoc.title}
                onChange={e => setNewDoc({...newDoc, title: e.target.value})}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
              <select
                value={newDoc.doc_type}
                onChange={e => setNewDoc({...newDoc, doc_type: e.target.value})}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              >
                <option value="equipment_standard">Норматив оснащения</option>
                <option value="job_description">Должностная инструкция</option>
                <option value="responsibility">Ответственность</option>
                <option value="inventory_procedure">Порядок инвентаризации</option>
                <option value="disposal_procedure">Порядок списания</option>
              </select>
              <input
                type="text"
                placeholder="Номер"
                value={newDoc.document_number}
                onChange={e => setNewDoc({...newDoc, document_number: e.target.value})}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
              <input
                type="date"
                value={newDoc.document_date}
                onChange={e => setNewDoc({...newDoc, document_date: e.target.value})}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
              <textarea
                placeholder="Содержание"
                value={newDoc.content}
                onChange={e => setNewDoc({...newDoc, content: e.target.value})}
                rows={3}
                className="col-span-2 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
              <label className="col-span-2 flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={newDoc.is_published}
                  onChange={e => setNewDoc({...newDoc, is_published: e.target.checked})}
                  className="rounded"
                />
                Опубликовать
              </label>
            </div>
            <button
              onClick={handleCreateDoc}
              className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm"
            >
              Создать документ
            </button>
          </div>

          {/* Documents List */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 border border-gray-100 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">Документы ({documents.length})</h2>
            {documents.length === 0 ? (
              <div className="text-center py-8 text-gray-500">Документов пока нет</div>
            ) : (
              <div className="space-y-2">
                {documents.map(doc => (
                  <div key={doc.id} className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded">
                    <div>
                      <div className="font-medium text-gray-900 dark:text-gray-100">{doc.title}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {docTypeLabels[doc.doc_type] || doc.doc_type} • {doc.document_number} • {doc.document_date}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {doc.is_published && <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">Опубликован</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Standards Tab */}
      {activeTab === 'standards' && (
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 border border-gray-100 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">Нормативы оснащения ({standards.length})</h2>
          {standards.length === 0 ? (
            <div className="text-center py-8 text-gray-500">Нормативов пока нет</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Должность</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Актив</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Кол-во</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Приоритет</th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {standards.map(s => (
                    <tr key={s.id}>
                      <td className="px-6 py-4 text-sm font-medium text-gray-900 dark:text-gray-100">{s.position_name}</td>
                      <td className="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">{s.asset_type_name}</td>
                      <td className="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">{s.quantity}</td>
                      <td className="px-6 py-4 text-sm">
                        <span className={`px-2 py-1 text-xs rounded-full ${s.priority === 1 ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300' : 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300'}`}>
                          {s.priority === 1 ? 'Обязательный' : 'Желательный'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Responsibilities Tab */}
      {activeTab === 'responsibilities' && (
        <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <h3 className="font-medium text-blue-900 dark:text-blue-300 mb-2">⚖️ Записи ответственности</h3>
          <p className="text-sm text-blue-800 dark:text-blue-400">
            Здесь фиксируются материально ответственные лица за подразделения и имущество.
            Для создания записи используйте API endpoint POST /api/regulatory/responsibilities
          </p>
        </div>
      )}
    </div>
  );
};

export default RegulatoryPage;
