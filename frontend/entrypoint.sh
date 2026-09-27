#!/bin/sh

DOMAIN="${LETSENCRYPT_DOMAIN:-}"
EMAIL="${LETSENCRYPT_EMAIL:-}"
ENABLE="${LETSENCRYPT_ENABLE:-true}"
CERT_FILE="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
WEBROOT="/var/www/certbot"
CHALLENGE_PORT=8888
DEFAULT_CONF="/etc/nginx/conf.d/default.conf"

echo "================================================"
echo " PAPI HTTPS Entry Point"
echo " Domain: $DOMAIN"
echo " Email: $EMAIL"
echo " HTTPS: $ENABLE (default: true)"
echo "================================================"

# Функция конвертации домена в punycode (для IDN доменов типа мастербайт.рф)
convert_to_punycode() {
    domain="$1"
    punycode=$(python3 -c "
import sys
try:
    domain = sys.argv[1]
    parts = domain.split('.')
    punycode_parts = []
    for part in parts:
        try:
            part.encode('ascii')
            punycode_parts.append(part)
        except UnicodeEncodeError:
            punycode_parts.append(part.encode('idna').decode('ascii'))
    print('.'.join(punycode_parts))
except Exception as e:
    print(domain, file=sys.stderr)
    print(domain)
" "$domain" 2>/dev/null)
    
    if [ -n "$punycode" ]; then
        echo "Конвертация домена в punycode..."
        echo "  $domain -> $punycode"
        echo "$punycode"
    else
        echo "$domain"
    fi
}

# Генерация полного nginx конфига с HTTPS
generate_full_conf() {
    local domain="$1"
    cat > "$DEFAULT_CONF" <<NGINX_EOF
# HTTP server — перенаправляем всё на HTTPS
server {
    listen 80;
    listen      [::]:80;

    server_name $domain www.$domain _;

    # ACME challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
        default_type "text/plain";
        allow all;
    }

    # Health check
    location = /health {
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }

    # Redirect to HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl;
    listen      [::]:443 ssl;

    server_name $domain www.$domain;

    # SSL сертификаты
    ssl_certificate     /etc/letsencrypt/live/$domain/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$domain/privkey.pem;

    # Настройки SSL
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache   shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

    # Безопасность
    add_header X-Frame-Options   "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    root /usr/share/nginx/html;
    index index.html;

    autoindex off;
    charset utf-8;
    client_max_body_size 100M;

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;

        proxy_no_cache 1;
        proxy_cache_bypass 1;
        add_header Cache-Control "no-store, no-cache, must-revalidate";
    }

    location = /api {
        return 301 /api/;
    }

    location ~ ^/(docs|redoc|openapi.json)\$ {
        proxy_pass http://backend:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location ~* ^/assets/.+\.(?:js|css|map|svg|png|jpe?g|gif|webp|avif|ico|woff2?|ttf|otf|eot)\$ {
        add_header Cache-Control "public, max-age=31536000, immutable";
        try_files \$uri =404;
    }

    location = /index.html {
        add_header Cache-Control "no-cache";
    }

    location / {
        try_files \$uri /index.html;
    }
}
NGINX_EOF
    echo "Full nginx config generated at $DEFAULT_CONF"
}

# Функция запуска временного HTTP-сервера для certbot challenge
start_challenge_server() {
    echo "Запуск challenge-сервера на порту $CHALLENGE_PORT..."
    cd "$WEBROOT"
    python3 -m http.server "$CHALLENGE_PORT" &
    CHALLENGE_PID=$!
    echo "Challenge-сервер запущен (PID: $CHALLENGE_PID)"
}

# Остановка challenge-сервера
stop_challenge_server() {
    if [ -n "$CHALLENGE_PID" ]; then
        echo "Остановка challenge-сервера..."
        kill "$CHALLENGE_PID" 2>/dev/null || true
        wait "$CHALLENGE_PID" 2>/dev/null || true
    fi
}

# Конвертируем домен в punycode если нужно
if [ -n "$DOMAIN" ]; then
    DOMAIN=$(convert_to_punycode "$DOMAIN")
    CERT_FILE="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
    echo "Итоговый домен: $DOMAIN"
fi

# HTTPS включён по умолчанию — проверяем сертификаты
echo "HTTPS включён. Проверяем сертификаты..."

HTTPS_OK=false

if [ -f "$CERT_FILE" ]; then
    echo "Сертификаты найдены. Проверяем срок действия..."
    EXPIRY=$(openssl x509 -in "$CERT_FILE" -noout -enddate 2>/dev/null | cut -d= -f2)
    EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s 2>/dev/null || echo "0")
    NOW_EPOCH=$(date +%s)
    DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))
    echo "Истекает: $EXPIRY ($DAYS_LEFT дней)"
    
    if [ "$DAYS_LEFT" -lt 30 ]; then
        echo "Обновление сертификата (осталось < 30 дней)..."
        start_challenge_server
        
        certbot renew --quiet --no-self-upgrade --deploy-hook "nginx -s reload"
        
        stop_challenge_server
        
        if [ $? -eq 0 ]; then
            echo "Сертификат обновлён."
            HTTPS_OK=true
        else
            echo "Предупреждение: обновление сертификата не удалось. Используем существующий."
            HTTPS_OK=true
        fi
    else
        echo "Сертификат действителен."
        HTTPS_OK=true
    fi
else
    echo "Сертификаты не найдены. Получаем от Let's Encrypt..."
    
    mkdir -p "$WEBROOT/.well-known/acme-challenge"
    
    start_challenge_server
    sleep 2
    
    certbot certonly \
        --webroot \
        --webroot-path="$WEBROOT" \
        --email="$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --force-renewal \
        --non-interactive \
        --redirect \
        --staple-ocsp \
        --preferred-challenges="http" \
        -d "$DOMAIN" \
        -d "www.$DOMAIN" \
        --key-type ecdsa
    
    stop_challenge_server
    CERTBOT_EXIT=$?
    
    if [ $CERTBOT_EXIT -eq 0 ]; then
        echo "Сертификаты успешно получены."
        HTTPS_OK=true
    else
        echo "ERROR: Не удалось получить сертификат (код: $CERTBOT_EXIT)."
        echo "Попытка подключения к HTTPS не удалась. Переходим в HTTP-режим."
        echo "Для активации HTTPS:"
        echo "  1. Настройте DNS A-record для $DOMAIN на IP сервера"
        echo "  2. Откройте порт 80 в фаерволе"
        echo "  3. Перезапустите: docker compose up -d --build"
        echo ""
        echo "Система запущена в HTTP-режиме. Проверьте логи для деталей."
    fi
fi

# Генерируем полный конфиг если HTTPS успешен
if [ "$HTTPS_OK" = true ]; then
    generate_full_conf "$DOMAIN"
    echo "HTTPS активирован."
else
    echo "HTTPS не активирован — нет сертификата. Работает HTTP."
fi

echo "Запускаем nginx..."
exec nginx -g "daemon off;"
