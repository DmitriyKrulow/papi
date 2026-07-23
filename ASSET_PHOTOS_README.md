# Загрузка фотографий активов

## API Endpoints

### `POST /api/assets/{id}/photos` - Загрузка фото актива

Загружает фотографию актива с метаданными.

#### Параметры (multipart/form-data):

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `file` | File | Yes | Загружаемое изображение |
| `stage` | string | No | Этап жизненного цикла: `receiving` (поступление), `inventory` (инвентаризация), `write_off` (списание), `repair` (ремонт), `maintenance` (ТО), `movement` (перемещение). По умолчанию: `other` |
| `description` | string | No | Описание фотографии |
| `taken_at` | string (datetime) | No | Время съемки |
| `taken_by` | integer | No | ID пользователя, сделавшего фото |
| `inventory_check_id` | integer | No | ID инвентаризации |
| `repair_request_id` | integer | No | ID заявки на ремонт |
| `is_before` | boolean | No | Фото до изменений. По умолчанию: `false` |
| `is_after` | boolean | No | Фото после изменений. По умолчанию: `false` |
| `sort_order` | integer | No | Порядок сортировки. По умолчанию: `0` |

#### Разрешенные типы файлов:
- Изображения: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- Документы: `.pdf`, `.doc`, `.docx`, `.xlsx`, `.xls`

#### Пример ответа:

```json
{
  "id": 1,
  "asset_id": 123,
  "document_id": 0,
  "uploaded_by": 1,
  "stage": "receiving",
  "description": "Фото при поступлении",
  "taken_at": "2026-07-24T00:00:00",
  "taken_by": null,
  "inventory_check_id": null,
  "repair_request_id": null,
  "is_before": false,
  "is_after": false,
  "sort_order": 0,
  "uploaded_at": "2026-07-24T00:01:00"
}
```

### `GET /api/assets/{id}/photos` - Получение всех фото актива

### `GET /api/asset-photos/{photo_id}` - Получение фото по ID

### `DELETE /api/asset-photos/{photo_id}` - Удаление фото

---

## Использование на фронтенде

### 1. Компонент загрузки

```tsx
import { AssetPhotoUpload } from '../components/assets/AssetPhotoUpload';
import { useAssetPhotos } from '../hooks/useAssetPhotos';

const AssetDetail = ({ assetId }) => {
  const { fetchPhotos } = useAssetPhotos(assetId);

  const handleUploadSuccess = (photo) => {
    console.log('Фото загружено:', photo);
    fetchPhotos();
  };

  return (
    <div>
      <AssetPhotoUpload
        assetId={assetId}
        stage="receiving"
        onUploadSuccess={handleUploadSuccess}
        allowedExtensions={['.jpg', '.jpeg', '.png', '.webp']}
        maxSizeMB={5}
      />
      
      {/* Список фото */}
      <AssetPhotoList assetId={assetId} />
    </div>
  );
};
```

### 2. Ручная загрузка через API

```typescript
import { useAssetPhotos } from '../hooks/useAssetPhotos';

const MyComponent = () => {
  const { uploadPhoto, loading, error } = useAssetPhotos(123);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const photo = await uploadPhoto(file, {
        stage: 'inventory',
        description: 'Фото при инвентаризации',
        is_before: true,
        is_after: false,
      });
      console.log('Фото загружено:', photo);
    } catch (err) {
      console.error('Ошибка:', err);
    }
  };

  return (
    <input 
      type="file" 
      accept="image/*" 
      onChange={handleFileChange} 
      disabled={loading}
    />
  );
};
```

### 3. Использование с FormData (чтобы увидеть пример загрузки через FormData из запроса)

```typescript
const formData = new FormData();
formData.append('file', file);
formData.append('stage', 'write_off');
formData.append('description', 'Фото перед списанием');
formData.append('is_before', 'true');
formData.append('is_after', 'false');

const response = await axios.post(`/api/assets/${assetId}/photos`, formData, {
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});
```

---

## Примеры сценариев

### 1. Фото при поступлении актива

```typescript
await uploadPhoto(file, {
  stage: 'receiving',
  description: 'Фото при поступлении в组织',
  is_before: true,
  is_after: false,
});
```

### 2. Фото при инвентаризации

```typescript
await uploadPhoto(file, {
  stage: 'inventory',
  description: 'Фото при текущей инвентаризации',
  inventory_check_id: inventoryId,
  is_before: true,
  is_after: false,
});
```

### 3. Фото перед списанием

```typescript
await uploadPhoto(file, {
  stage: 'write_off',
  description: 'Фото актива перед списанием',
  is_before: true,
  is_after: false,
});
```

### 4. Фото "До" и "После" ремонта

```typescript
// Фото до ремонта
await uploadPhoto(beforeFile, {
  stage: 'repair',
  description: 'Фото до ремонта',
  repair_request_id: repairId,
  is_before: true,
  is_after: false,
});

// Фото после ремонта
await uploadPhoto(afterFile, {
  stage: 'repair',
  description: 'Фото после ремонта',
  repair_request_id: repairId,
  is_before: false,
  is_after: true,
});
```

---

## Структура проекта

### Backend

```
backend/
└── src/
    ├── core/
    │   └── entities/
    │       └── asset_photo.py          # Сущность AssetPhoto
    ├── infrastructure/
    │   └── db/
    │       ├── models/
    │       │   └── asset_photo.py      # SQLAlchemy модель
    │       └── repositories/
    │           └── asset_photo_repository.py  # Репозиторий
    ├── presentation/
    │   └── http/
    │       ├── routers/
    │       │   └── asset_photos.py     # API роутеры
    │       └── schemas/
    │           └── asset_photos.py     # Pydantic схемы
    └── use_cases/
        └── asset_photo/
            └── upload_asset_photo.py   # Сервис загрузки
```

### Frontend

```
frontend/
└── src/
    ├── api/
    │   └── client.ts                   # API клиент с методами для photos
    ├── hooks/
    │   └── useAssetPhotos.ts           # Хук для работы с фото
    └── components/
        └── assets/
            ├── AssetPhotoUpload.tsx    # Компонент загрузки фото
            ├── AssetPhotoList.tsx      # Компонент списка фото
            └── AssetPhotoUpload.module.css
```

---

## Схема этапов (stage)

| Код | Описание | Использование |
|-----|----------|---------------|
| `receiving` | При поступлении | При приемке нового актива |
| `inventory` | При инвентаризации | Во время плановой/внеплановой инвентаризации |
| `write_off` | Перед списанием | Перед списанием актива |
| `repair` | Во время ремонта | Во время и после ремонта |
| `maintenance` | Во время ТО | Во время технического обслуживания |
| `movement` | При перемещении | При перемещении актива |
| `other` | Другое | Для прочих случаев |

---

## Именование файлов

- Файлы сохраняются в `backend/uploads/assets/`
- Имя файла: `UUID{расширение}`
- Пример: `a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg`

---

## Проверка MIME-типа

При загрузке проверяется MIME-тип файла. Если тип не соответствует разрешенным, возвращается ошибка 400.
