# tests/README.md
# Тестирование

## Структура

```
tests/
├── __init__.py
├── conftest.py           # Общие настройки и фикстуры
├── requirements.txt      # Зависимости для тестов
├── unit/                 # Юнит-тесты
│   ├── __init__.py
│   ├── conftest.py       # Фикстуры для юнит-тестов
│   ├── test_asset.py     # Тесты актива
│   ├── test_user.py      # Тесты пользователя
│   ├── test_document.py  # Тесты документа
│   ├── test_department.py # Тесты подразделения
│   ├── test_repair.py    # Тесты заявки на ремонт
│   └── test_value_objects.py # Тесты value objects
├── integration/          # Интеграционные тесты
│   └── __init__.py
└── e2e/                  # E2E тесты
    └── __init__.py
```

## Запуск тестов

### Установка зависимостей
```bash
pip install -r tests/requirements.txt
```

### Запуск всех тестов
```bash
pytest tests/ -v
```

### Запуск только юнит-тестов
```bash
pytest tests/unit/ -v
```

### Запуск конкретного тестового файла
```bash
pytest tests/unit/test_asset.py -v
```

### Запуск с покрытием кода
```bash
pytest tests/unit/ -v --cov=src --cov-report=html
```

## Принципы написания тестов

1. **Юнит-тесты** тестируют отдельные сущности и value objects
2. **Интеграционные тесты** проверяют взаимодействие с БД и внешними сервисами
3. **E2E тесты** проверяют полный пользовательский путь

## Покрытие кода

Целевое покрытие: **80%**
