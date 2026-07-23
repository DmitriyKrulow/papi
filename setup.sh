#!/bin/bash

# PAPI - Установка и настройка

echo "=========================================="
echo "PAPI - Установка зависимостей"
echo "=========================================="

# Проверка Python
echo "Проверка Python..."
python --version

# Установка зависимостей backend
echo ""
echo "Установка зависимостей backend..."
cd backend
pip install -r requirements.txt
cd ..

# Создание структуры данных
echo ""
echo "Создание структуры данных..."
mkdir -p backend/data

# Запуск backend
echo ""
echo "=========================================="
echo "Backend успешно установлен!"
echo "=========================================="
echo ""
echo "Для запуска backend выполните:"
echo "  cd backend"
echo "  python -m src.infrastructure.main"
echo ""
echo "По умолчанию:"
echo "  - Backend будет запущен на порту 8888"
echo "  - Первый запуск создаст администратора с учетными данными:"
echo "    Username: admin"
echo "    Password: admin123"
echo "  - Данные пользователей сохраняются в backend/data/users.json"
echo ""
