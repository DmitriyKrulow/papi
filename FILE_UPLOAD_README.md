# Загрузка файлов # Бэкенд

## API Endpoints

### `POST /api/documents/upload` - Загрузка файла

Загружает файл на сервер с дополнительными метаданными.

#### Параметры (multipart/form-data):

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `file` | File | Yes | Загружаемый файл |
| `document_type` | string | No | Тип документа (photo, scan, contract, invoice, act, warranty, passport, manual, certificate, report, other). По умолчанию: `other` |
| `category` | string | No | Категория документа (asset, repair, inventory, movement, write_off, contract, supplier, employee). По умолчанию: `asset` |
| `entity_id` | integer | No | ID сущности, к которой привязывается документ |
| `entity_type` | string | No | Тип сущности (asset, repair, etc.) |
| `title` | string | No | Заголовок документа |
| `description` | string | No | Описание документа |
| `is_primary` | boolean | No | Является ли документ основным. По умолчанию: `false` |
| `sort_order` | integer | No | Порядок сортировки. По умолчанию: `0` |

#### Разрешенные типы файлов:
- Excel: `.xlsx`, `.xls`
- PDF: `.pdf`
- Изображения: `.jpg`, `.jpeg`, `.png`, `.gif`
- Word: `.doc`, `.docx`

#### Пример ответа:

```json
{
  "id": 1,
  "filename": "document.xlsx",
  "file_path": "uploads/documents/abc123def456.xlsx",
  "file_size": 102400,
  "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "uploaded_by": 1,
  "document_type": "other",
  "category": "asset",
  "entity_id": null,
  "entity_type": null,
  "title": null,
  "description": null,
  "uploaded_at": "2026-07-23T23:55:25+03:00",
  "is_primary": false,
  "sort_order": 0,
  "file_hash": null
}
```

### `GET /api/documents` - Получение всех документов

#### Пример ответа:

```json
{
  "total": 1,
  "items": [
    {
      "id": 1,
      "filename": "document.xlsx",
      "file_path": "uploads/documents/abc123def456.xlsx",
      "file_size": 102400,
      "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "uploaded_by": 1,
      "document_type": "other",
      "category": "asset",
      "entity_id": null,
      "entity_type": null,
      "title": null,
      "description": null,
      "uploaded_at": "2026-07-23T23:55:25+03:00",
      "is_primary": false,
      "sort_order": 0,
      "file_hash": null
    }
  ]
}
```

### `GET /api/documents/{document_id}` - Получение документа по ID

### `DELETE /api/documents/{document_id}` - Удаление документа

---

# Фронтенд

## Использование

### 1. Загрузка файла через FormData

```typescript
import { useDocuments } from '../hooks/useDocuments';

const MyComponent = () => {
  const { uploadDocument, loading, error } = useDocuments();

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const document = await uploadDocument(file, {
        document_type: 'photo',
        category: 'asset',
        entity_id: 123,
        entity_type: 'asset',
        title: 'Фото актива',
        description: 'Фотография основного средства',
        is_primary: true,
        sort_order: 0,
      });
      console.log('Файл загружен:', document);
    } catch (err) {
      console.error('Ошибка загрузки:', err);
    }
  };

  return (
    <input 
      type="file" 
      onChange={handleFileUpload} 
      disabled={loading}
    />
  );
};
```

### 2. Использование компонента FileUpload

```typescript
import { FileUpload } from '../components/documents/FileUpload';
import { useDocuments } from '../hooks/useDocuments';

const MyComponent = () => {
  const { fetchDocuments } = useDocuments();

  return (
    <FileUpload
      onUploadSuccess={(document) => {
        console.log('Файл загружен:', document);
        fetchDocuments();
      }}
      allowedExtensions={['.xlsx', '.pdf', '.jpg', '.png']}
      maxSizeMB={10}
    />
  );
};
```

### 3. Загрузка сущности (например, актива)

```typescript
import { useDocuments } from '../hooks/useDocuments';

const AssetForm = ({ assetId }: { assetId: number }) => {
  const { uploadDocument, loading } = useDocuments();

  const handleAssetPhotoUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', 'photo');
    formData.append('category', 'asset');
    formData.append('entity_id', String(assetId));
    formData.append('entity_type', 'asset');
    formData.append('title', 'Фото актива');
    formData.append('is_primary', 'true');

    try {
      await uploadDocument(file, {
        document_type: 'photo',
        category: 'asset',
        entity_id: assetId,
        entity_type: 'asset',
        title: 'Фото актива',
        is_primary: true,
      });
    } catch (err) {
      console.error('Ошибка:', err);
    }
  };

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      const fileInput = e.target.elements.namedItem('photo') as HTMLInputElement;
      if (fileInput.files?.[0]) {
        handleAssetPhotoUpload(fileInput.files[0]);
      }
    }}>
      <input type="file" name="photo" accept="image/*" />
      <button type="submit" disabled={loading}>Загрузить фото</button>
    </form>
  );
};
```

---

## Структура проекта

### Backend

```
backend/
└── src/
    ├── core/
    │   └── entities/
    │       └── document.py          # Сущность Document
    ├── infrastructure/
    │   └── db/
    │       ├── models/
    │       │   └── document.py      # SQLAlchemy модель
    │       └── repositories/
    │           └── document_repository.py  # Репозиторий
    ├── presentation/
    │   └── http/
    │       ├── routers/
    │       │   └── documents.py     # API роутеры
    │       └── schemas/
    │           └── documents.py     # Pydantic схемы
    └── use_cases/
        └── document/
            └── upload_document.py   # Сервис загрузки
```

### Frontend

```
frontend/
└── src/
    ├── api/
    │   └── client.ts                # API клиент с методом upload
    ├── hooks/
    │   └── useDocuments.ts          # Хук для работы с документами
    └── components/
        └── documents/
            ├── FileUpload.tsx       # Компонент загрузки файлов
            └── AssetDocuments.tsx   # Пример использования
```

---

## Исправление ошибок CORS

Если возникает ошибка CORS при загрузке файлов, убедитесь, что в `main.py` настроен CORS для разрешения запросов с фронтенда:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Примечания

1. Файлы сохраняются в директорию `backend/uploads/documents/`
2. Имена файлов генерируются как UUID с исходным расширением
3. MIME-тип проверяется для безопасности
4. Размер файла ограничен по умолчанию (в коде можно настроить)
5. Документы можно привязывать к сущностям через `entity_id` и `entity_type`
