import { useState } from 'react';
import { FileUpload } from './FileUpload';
import { useDocuments } from '../hooks/useDocuments';

interface AssetDocumentsProps {
  assetId: number;
}

export const AssetDocuments = ({ assetId }: AssetDocumentsProps) => {
  const [selectedEntity, setSelectedEntity] = useState<number | null>(null);
  const { documents, fetchDocuments, deleteDocument, error } = useDocuments();

  const handleUploadSuccess = (document: any) => {
    console.log('Document uploaded:', document);
    fetchDocuments();
  };

  const handleDelete = async (documentId: number) => {
    try {
      await deleteDocument(documentId);
      console.log('Document deleted successfully');
    } catch (err) {
      console.error('Failed to delete document:', err);
    }
  };

  const getDocumentIcon = (mime: string) => {
    if (mime.startsWith('image/')) return '🖼️';
    if (mime === 'application/pdf') return '📄';
    if (mime.includes('excel') || mime.includes('spreadsheet')) return '📊';
    if (mime.includes('word') || mime.includes('document')) return '📝';
    return '📁';
  };

  const getDocumentTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      photo: 'Фото',
      scan: 'Скан',
      contract: 'Договор',
      invoice: 'Счет',
      act: 'Акт',
      warranty: 'Гарантия',
      passport: 'Паспорт',
      manual: 'Руководство',
      certificate: 'Сертификат',
      report: 'Отчет',
      other: 'Другое',
    };
    return labels[type] || type;
  };

  return (
    <div className="asset-documents">
      <h3>Документы актива #{assetId}</h3>
      
      {error && <div className="error">{error}</div>}
      
      <div className="upload-section">
        <h4>Загрузить документ</h4>
        <FileUpload
          onUploadSuccess={handleUploadSuccess}
          allowedExtensions={['.xlsx', '.xls', '.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']}
          maxSizeMB={10}
        />
      </div>
      
      <div className="document-list">
        <h4>Список документов ({documents.length})</h4>
        
        {documents.length === 0 ? (
          <p className="no-documents">Нет загруженных документов</p>
        ) : (
          <ul>
            {documents.map((doc) => (
              <li key={doc.id} className="document-item">
                <span className="icon">{getDocumentIcon(doc.mime_type)}</span>
                <div className="info">
                  <strong className="name">{doc.filename}</strong>
                  <div className="meta">
                    <span>{getDocumentTypeLabel(doc.document_type)}</span>
                    <span>•</span>
                    <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
                    <span>•</span>
                    <span>{new Date(doc.uploaded_at).toLocaleDateString('ru-RU')}</span>
                  </div>
                </div>
                <button onClick={() => handleDelete(doc.id)} className="delete-btn">
                  🗑️ Удалить
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};
