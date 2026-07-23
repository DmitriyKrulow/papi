# PAPI - Система управления активами

Система для управления основными средствами и активами предприятия.

## Установка

### Windows

```bash
setup.bat
```

### Linux/Mac

```bash
chmod +x setup.sh
./setup.sh
```

### Ручная установка

```bash
# Backend
cd backend
pip install -r requirements.txt

# Создание структуры данных
mkdir -p backend/data
```

## Запуск

### Backend

```bash
cd backend
python -m src.infrastructure.main
```

Backend будет доступен на `http://localhost:8888`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend будет доступен на `http://localhost:5173`

## Учетные данные начального администратора

При первом запуске автоматически создается администратор:

- **Username:** `admin`
- **Password:** `admin123`

**ВАЖНО:** После первого входа рекомендуется сменить пароль!

## Структура данных

Пользователи хранятся в файле `backend/data/users.json` в формате JSON.

## Эндпоинты API

### Аутентификация

- `POST /api/auth/register` - Регистрация нового пользователя
- `POST /api/auth/login` - Вход в систему
- `GET /api/auth/me` - Получение информации о текущем пользователе
- `PUT /api/auth/profile` - Обновление профиля
- `POST /api/auth/change-password` - Смена пароля

### Управление пользователями (только для администраторов)

- `GET /api/admin/users` - Получение всех пользователей
- `DELETE /api/admin/users/{user_id}` - Удаление пользователя
- `PUT /api/admin/users/{user_id}/role?role={role}` - Изменение роли пользователя

### Панели администратора

- `GET /api/admin/users` - Получение списка всех пользователей
- `DELETE /api/admin/users/{user_id}` - Удаление пользователя
- `PUT /api/admin/users/{user_id}/role?role=admin` - Назначение администратора

## Технологии

### Backend
- Python 3.8+
- FastAPI
- SQLAlchemy
- Pydantic
- JWT (python-jose)
- PBKDF2 для хеширования паролей

### Frontend
- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Axios

## Структура проекта

```
papi/
├── backend/
│   ├── src/
│   │   ├── core/
│   │   │   ├── entities/
│   │   │   ├── value_objects/
│   │   │   └── security/
│   │   ├── infrastructure/
│   │   │   ├── db/
│   │   │   └── main.py
│   │   └── presentation/
│   │       └── http/
│   │           └── routers/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   └── forms/
│   │   ├── pages/
│   │   ├── context/
│   │   ├── hooks/
│   │   └── api/
│   └── package.json
└── README.md
```

## Безопасность

- Пароли хешируются с помощью PBKDF2
- Используются JWT-токены для аутентификации
- Администраторы имеют специальные права доступа
- Валидация всех входных данных
- Protection от timing attacks при сравнении паролей

## Файлы, которые были изменены/созданы

### Backend
- `backend/src/presentation/http/routers/auth.py` - Эндпоинты аутентификации
- `backend/src/presentation/http/routers/users.py` - Управление пользователями
- `backend/src/presentation/http/routers/admin.py` - Админ-панель
- `backend/src/presentation/http/schemas/auth.py` - Схемы для аутентификации
- `backend/src/presentation/http/schemas/users.py` - Схемы для пользователей
- `backend/src/infrastructure/db/repositories/user_repository.py` - Репозиторий пользователей
- `backend/src/use_cases/auth/register_user.py` - Используемый случай регистрации
- `backend/src/use_cases/auth/login_user.py` - Используемый случай входа
- `backend/src/use_cases/admin/initial_setup.py` - Начальная настройка
- `backend/src/core/security/jwt_handler.py` - Обработка JWT токенов
- `backend/data/users.json` - Хранилище данных (создается автоматически)

### Frontend
- `frontend/src/context/AuthContext.tsx` - Контекст аутентификации
- `frontend/src/components/forms/LoginForm.tsx` - Форма входа
- `frontend/src/components/forms/RegisterForm.tsx` - Форма регистрации
- `frontend/src/components/forms/ProfileForm.tsx` - Форма профиля
- `frontend/src/components/common/Navbar.tsx` - Обновлен навбар с админ-ссылкой
- `frontend/src/pages/Login.tsx` - Страница входа
- `frontend/src/pages/Register.tsx` - Страница регистрации
- `frontend/src/pages/Profile.tsx` - Страница профиля
- `frontend/src/pages/AdminPanel.tsx` - Админ-панель
- `frontend/src/pages/Dashboard.tsx` - Дашборд с проверкой аутентификации
- `frontend/src/App.tsx` - Обновлен с роутом админ-панели

## Известные проблемы

1. При первом запуске убедитесь, что порт 8888 свободен
2. Если users.json поврежден, удалите его и перезапустите backend

## Поддержка

Для получения помощи обратитесь к документации API по адресу:
`http://localhost:8888/docs`
