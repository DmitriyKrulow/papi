#!/bin/bash
# install-https.sh — Установка HTTPS с Let's Encrypt на Ubuntu
# Запустите: sudo bash install-https.sh

set -e

DOMAIN="${1:-мастербайт.рф}"
EMAIL="${2:-admin@example.com}"

echo "============================================"
echo " Установка HTTPS с Let's Encrypt"
echo " Домен: $DOMAIN"
echo " Email: $EMAIL"
echo "============================================"

# 1. Проверяем, что домен указывает на сервер
echo ""
echo "[1/5] Проверка DNS..."
if ! dig +short "$DOMAIN" | grep -q "$(curl -s ifconfig.me)"; then
    echo "⚠️  ВНИМАНИЕ: Домен $DOMAIN не указывает на этот сервер!"
    echo "    Текущий IP: $(curl -s ifconfig.me)"
    echo "    DNS запись: $(dig +short $DOMAIN)"
    echo ""
    echo "    Сначала настройте DNS-запись A для $DOMAIN"
    read -p "    Продолжить? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Отменено."
        exit 1
    fi
fi
echo "✓ DNS настроен правильно"

# 2. Останавливаем текущий nginx, если он запущен на хосте
echo ""
echo "[2/5] Остановка хостового nginx..."
if systemctl is-active --quiet nginx; then
    sudo systemctl stop nginx
    sudo systemctl disable nginx
    echo "✓ Хостовый nginx остановлен"
else
    echo "✓ Хостовый nginx не запущен"
fi

# 3. Проверяем, что Docker запущен
echo ""
echo "[3/5] Проверка Docker..."
if ! docker info &>/dev/null; then
    echo "❌ Docker не запущен. Установите Docker:"
    echo "   curl -fsSL https://get.docker.com | sudo sh"
    exit 1
fi
echo "✓ Docker запущен"

# 4. Настраиваем .env для HTTPS
echo ""
echo "[4/5] Настройка .env..."

# Проверяем, есть ли HTTPS_PORT в .env
if ! grep -q "HTTPS_PORT" .env 2>/dev/null; then
    echo "" >> .env
    echo "# HTTPS настройки" >> .env
    echo "LETSENCRYPT_DOMAIN=$DOMAIN" >> .env
    echo "LETSENCRYPT_EMAIL=$EMAIL" >> .env
    echo "LETSENCRYPT_ENABLE=true" >> .env
    echo "HTTPS_PORT=443" >> .env
    echo "✓ HTTPS настройки добавлены в .env"
else
    # Обновляем существующие
    sed -i "s/^LETSENCRYPT_DOMAIN=.*/LETSENCRYPT_DOMAIN=$DOMAIN/" .env
    sed -i "s/^LETSENCRYPT_EMAIL=.*/LETSENCRYPT_EMAIL=$EMAIL/" .env
    sed -i "s/^LETSENCRYPT_ENABLE=.*/LETSENCRYPT_ENABLE=true/" .env
    sed -i "s/^HTTPS_PORT=.*/HTTPS_PORT=443/" .env
    echo "✓ HTTPS настройки обновлены в .env"
fi

# 5. Перезапускаем сервисы с HTTPS
echo ""
echo "[5/5] Перезапуск сервисов с HTTPS..."
docker compose down
docker compose up -d --build

echo ""
echo "============================================"
echo " ✓ HTTPS успешно настроен!"
echo "============================================"
echo ""
echo "  HTTP:  http://$DOMAIN"
echo "  HTTPS: https://$DOMAIN"
echo ""
echo "  Проверка:"
echo "    curl -I https://$DOMAIN"
echo ""
echo "  Управление:"
echo "    docker compose up -d              # Запуск"
echo "    docker compose down               # Остановка"
echo "    docker logs papi-frontend         # Логи (включая certbot)"
echo "============================================"

# Добавляем автообновление в crontab
echo ""
echo "Настройка автообновления сертификатов..."
(crontab -l 2>/dev/null | grep -v "certbot renew"; echo "0 */12 * * * docker compose exec -T papi-frontend certbot renew --quiet --no-self-upgrade --deploy-hook 'nginx -s reload' >> /var/log/certbot-renew.log 2>&1") | crontab -
echo "✓ Автообновление добавлено в crontab (каждые 12 часов)"

echo ""
# Примечание: автообновление сертификатов теперь встроено в entrypoint.sh
# При каждом запуске контейнера проверяется срок действия сертификата
# и при необходимости (< 30 дней) он обновляется автоматически.
# Crontab можно использовать для принудительного обновления:
# docker compose exec -T papi-frontend certbot renew --quiet --no-self-upgrade

echo "Готово! Откройте https://$DOMAIN в браузере"
