#!/bin/bash
# renew-certs.sh — скрипт для обновления сертификатов Let's Encrypt
# Запускается из crontab на хосте или внутри контейнера

set -e

CERTBOT_DIR="/etc/letsencrypt"
LOG_FILE="/var/log/certbot-renew.log"

echo "$(date '+%Y-%m-%d %H:%M:%S') — Начало обновления сертификатов" >> "$LOG_FILE"

# Обновляем сертификаты (автоматический режим с nginx hook)
certbot renew --quiet --no-self-upgrade --deploy-hook "nginx -s reload" 2>> "$LOG_FILE"

if [ $? -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') — Сертификаты обновлены успешно" >> "$LOG_FILE"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') — Ошибка обновления сертификатов" >> "$LOG_FILE"
    exit 1
fi
