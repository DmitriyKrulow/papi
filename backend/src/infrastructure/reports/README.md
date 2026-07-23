# Генерация отчетов

## Структура

```
backend/src/infrastructure/reports/
├── __init__.py           # Инициализация пакета
├── base.py               # Базовый класс для генераторов
├── utils.py              # Вспомогательные функции
├── asset_report.py       # Отчет по активам
├── depreciation_report.py # Отчет по амортизации
└── inventory_report.py   # Отчет по инвентаризации
```

## Зависимости

```bash
pip install pandas openpyxl
```

## Использование

### 1. Базовый класс

Все генераторы наследуются от `BaseReportGenerator`:

```python
from backend.src.infrastructure.reports.base import BaseReportGenerator

class CustomReportGenerator(BaseReportGenerator):
    def generate(self, data, **kwargs) -> bytes:
        # Генерация отчета
        self._add_sheet("Sheet1", df)
        return self.save_bytes()
```

### 2. Генерация отчетов

#### Отчет по активам

```python
from backend.src.infrastructure.reports import AssetReportGenerator

generator = AssetReportGenerator()
report_bytes = generator.generate(
    assets=assets_data,
    include_photos=False,
    include_history=False
)
```

#### Отчет по амортизации

```python
from backend.src.infrastructure.reports import DepreciationReportGenerator

generator = DepreciationReportGenerator()
report_bytes = generator.generate(
    assets=assets_data,
    depreciation_records=records,
    report_date="2026-07-24"
)
```

#### Отчет по инвентаризации

```python
from backend.src.infrastructure.reports import InventoryReportGenerator

generator = InventoryReportGenerator()
report_bytes = generator.generate(
    inventory_check_id=123,
    assets=assets_data,
    results=check_results
)
```

## API Endpoints

### `GET /api/reports/list` - Список отчетов

### `GET /api/reports/asset-report` - Отчет по активам

Параметры:
- `include_photos` - включить фотографии (по умолчанию: `false`)
- `include_history` - включить историю (по умолчанию: `false`)

### `GET /api/reports/depreciation-report` - Отчет по амортизации

Параметры:
- `report_date` - дата отчета (формат: `YYYY-MM-DD`)

### `GET /api/reports/inventory-report/{check_id}` - Отчет по инвентаризации

Параметры:
- `check_id` - ID инвентаризации

## Листы отчетов

### Отчет по активам

- **Сводка** - общая информация и статистика
- **Активы** - детальный список всех активов
- **По подразделениям** - сгруппировано по департаментам
- **По статусам** - сгруппировано по статусам

### Отчет по амортизации

- **Сводка** - общая информация
- **Амортизация** - детальный расчет амортизации
- **По категориям** - сгруппировано по типам активов

### Отчет по инвентаризации

- **Сводка** - информация об инвентаризации
- **Активы** - список активов
- **Расхождения** - выявленные проблемы

## Вспомогательные функции

```python
from backend.src.infrastructure.reports.utils import (
    format_currency,
    format_date,
    calculate_depreciation,
    pivot_data,
    filter_by_date_range
)
```

## Форматирование

- **Валюта**: `100 000,00` (пробел как разделитель тысяч)
- **Даты**: `ДД.ММ.ГГГГ`
- **Листы**: Имена на русском языке
- **Стили**: Заголовки жирным, шапка синяя, границы
