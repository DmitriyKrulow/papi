#!/bin/bash
# get-certs.sh — получение/обновление сертификатов Let's Encrypt
# Запускается один раз при первом запуске или при необходимости

set -e

DOMAIN="${1:-мастербайт.рф}"
EMAIL="${2:-admin@example.com}"
CERTBOT_DIR="/etc/letsencrypt"
WEBROOT="/var/www/certbot"

echo "Получение сертификатов для домена: $DOMAIN"
echo "Email для уведомлений: $EMAIL"

# Создаём директорию для challenge-файлов
mkdir -p "$WEBROOT/.well-known/acme-challenge"

# Получаем/обновляем сертификаты
certbot certonly \
    --webroot \
    --webroot-path="$WEBROOT" \
    --email="$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --non-interactive \
    --redirect \
    --staple-ocsp \
    --preferred-challenges="http" \
    --key-type ecdsa

echo "Сертификаты успешно получены:"
echo "  SSL Cert: $CERTBOT_DIR/live/$DOMAIN/fullchain.pem"
echo "  SSL Key:  $CERTBOT_DIR/live/$DOMAIN/privkey.pem"
echo ""
echo "Срок действия: $(openssl x509 -in $CERTBOT_DIR/live/$DOMAIN/cert.pem -noout -enddate 2>/dev/null || echo 'N/A')"
