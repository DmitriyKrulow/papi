# HTTPS с Let's Encrypt

## Описание

Автоматическое получение и обновление SSL-сертификатов от Let's Encrypt (бесплатно, на 90 дней с автопродлением).

**HTTPS включён по умолчанию.** Система всегда пытается подключиться по HTTPS и переключается на HTTP только если получение сертификата невозможно.

## Быстрый старт

### 1. Настройка домена

Убедитесь, что ваш домен указывает на IP сервера:
```bash
# Проверка
dig +short мастербайт.рф

# Должно вернуть IP вашего сервера
```

### 2. Активация HTTPS (два способа)

#### Способ 1: Через админ-панель (рекомендуется)
1. Войдите в систему как администратор
2. Перейдите в **Админ-панель → HTTPS**
3. Введите доменное имя и email
4. Нажмите **"Сохранить настройки"**
5. Нажмите **"Перезапустить frontend"**

#### Способ 2: Через .env файл
```bash
# 1. Отредактируйте .env:
LETSENCRYPT_ENABLE=true
LETSENCRYPT_DOMAIN=мастербайт.рф
LETSENCRYPT_EMAIL=admin@example.com

# 2. Перезапустите (сертификаты получатся автоматически):
docker compose down
docker compose up -d --build
```

> **Примечание:** При первом запуске контейнер frontend может запуститься дольше обычного (1-2 минуты) — это время получения сертификатов от Let's Encrypt.

## Как это работает

### Архитектура

```
Клиент
   ↓ HTTP (80) → HTTPS редирект
Nginx (frontend контейнер)
   ↓ HTTPS (443)
   ↓ HTTP (8000)
Backend (FastAPI)
```

### Автополучение сертификатов

1. При запуске контейнер `papi-frontend` проверяет переменную `LETSENCRYPT_ENABLE`
2. Если `true` — запускает entrypoint.sh, который:
   - Конвертирует домен в punycode (мастербайт.рф → xn--80a1af1atq.xn--p1ai)
   - Проверяет наличие существующих сертификатов
   - Если сертификатов нет — запускает временный HTTP-сервер на порту 8888
   - Certbot использует webroot-метод для challenge-верификации
   - Сертификаты сохраняются в volume `certdata`
   - Генерируется nginx-конфиг с правильным доменом через `envsubst`
   - Запускается nginx с HTTPS
3. При ошибке получения сертификатов система автоматически падает в HTTP-режим

### Автообновление

- Certbot встроен в контейнер `papi-frontend`
- При запуске проверяется срок действия сертификата
- Если осталось < 30 дней — сертификат обновляется автоматически
- После обновления происходит automatic nginx reload

### Настройки из UI

- Все HTTPS-настройки хранятся в БД и доступны через админ-панель
- При сохранении настроек автоматически обновляется `.env` файл
- Для применения изменений перезапустите frontend контейнер

## Настройка в .env

```bash
# HTTPS включён по умолчанию
LETSENCRYPT_ENABLE=true

# Домен (должен указывать на IP сервера)
LETSENCRYPT_DOMAIN=мастербайт.рф

# Email для уведомлений
LETSENCRYPT_EMAIL=admin@example.com

# HTTPS порт
HTTPS_PORT=443
```

## Админ-панель

### Вкладка "HTTPS"

Доступна в админ-панели (требуется роль admin):

- **Статус HTTPS** — показывает текущий статус сертификатов
- **Включить HTTPS** — переключатель вкл/выкл
- **Доменное имя** — домен для сертификата (автоматически конвертируется в punycode)
- **Email** — email для уведомлений Let's Encrypt
- **HTTPS порт** — порт для HTTPS (обычно 443)
- **Перезапустить frontend** — применяет настройки

### API endpoints

```bash
# Получить настройки
GET /api/system-settings/config

# Сохранить настройки
POST /api/system-settings/config

# Перезапустить frontend
POST /api/system-settings/restart-https

# Проверить статус HTTPS
GET /api/system-settings/https-status
```

## Команды

### Запуск с HTTPS

```bash
# Отредактируйте .env (LETSENCRYPT_ENABLE=true)
docker compose down
docker compose up -d --build
```

### Проверка статуса сертификатов

```bash
# Внутри контейнера
docker exec papi-frontend certbot certificates

# На хосте
docker logs papi-frontend | grep -i certbot
```

### Принудительное обновление

```bash
docker exec papi-frontend certbot renew --force-renewal
```

### Логи

```bash
# Логи получения сертификатов
docker logs papi-frontend

# Логи обновления (crontab)
tail -f /var/log/certbot-renew.log
```

## Troubleshooting

### Ошибка: "Certificate is about to expire"

```bash
# Проверка статуса
docker exec papi-frontend certbot certificates

# Принудительное обновление
docker exec papi-frontend certbot renew --force-renewal
```

### Ошибка: "Challenge failed"

1. Проверьте DNS-запись A для домена
2. Убедитесь, что порт 80 открыт на сервере
3. Проверьте, что nginx запущен:
   ```bash
   docker logs papi-frontend
   ```

### Ошибка: "Port 80 already in use"

Остановите хостовый nginx:
```bash
sudo systemctl stop nginx
sudo systemctl disable nginx
```

### Ошибка: "Connection refused" на порту 80

Проверьте, что контейнер запущен:
```bash
docker ps | grep frontend
docker logs papi-frontend
```

### Система работает в HTTP-режиме

Это означает, что не удалось получить HTTPS-сертификат. Проверьте:
1. DNS A-запись для домена указывает на IP сервера
2. Порт 80 открыт на сервере и не заблокирован фаерволом
3. Нет конфликта портов (другой сервис не занимает порт 80)
4. Перезапустите: `docker compose restart frontend`

## Безопасность

- ✅ TLS 1.2+ только
- ✅ HSTS включён (63072000 секунд)
- ✅ OCSP Stapling
- ✅ Strong cipher suites (ECDHE)
- ✅ HTTP → HTTPS редирект
- ✅ ECDSA ключи (более безопасные чем RSA)

## Лимиты Let's Encrypt

- 50 сертификатов в неделю на домен
- 300 доменов в неделю на аккаунт
- Сертификат действителен 90 дней
- Автообновление работает при >30 дней до истечения

## Мониторинг

```bash
# Проверка срока действия
openssl s_client -connect мастербайт.рф:443 -servername мастербайт.рф </dev/null 2>/dev/null | openssl x509 -noout -dates

# Логи certbot
docker logs papi-frontend

# Логи обновления
tail -f /var/log/certbot-renew.log
```

## Отключение HTTPS

```bash
# Через админ-панель:
# 1. Перейдите в Админ-панель → HTTPS
# 2. Отключите "Включить HTTPS"
# 3. Нажмите "Перезапустить frontend"

# Или через .env:
LETSENCRYPT_ENABLE=false
docker compose restart frontend
```
