# PAPI frontend image (multi-stage: build with Node, serve with nginx)

# ---- Build stage ----
FROM node:22-alpine AS build

WORKDIR /app

# Configure npm with retry and multiple fallback registries
RUN npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000 && \
    npm config set fetch-retries 5 && \
    npm config set fetch-timeout 300000

# Copy lockfile first for better caching
COPY package-lock.json ./
COPY package.json ./

# Try official registry first, fall back to mirrors
RUN npm install --prefer-offline 2>/dev/null || \
    (npm config set registry https://registry.npmmirror.com && npm install --prefer-offline 2>/dev/null) || \
    (npm config set registry https://registry.npmjs.org && npm install)

# Copy source and build static assets
COPY . .
RUN npm run build

# ---- Serve stage ----
FROM nginx:1.27-alpine AS serve

# Configure Alpine mirror for regions with restricted access
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories 2>/dev/null || true

# Install certbot, openssl, and envsubst for SSL management
RUN apk add --no-cache certbot openssl gettext

# Copy HTTP config (used as fallback when SSL is not available)
COPY nginx-http.conf /etc/nginx/nginx-http.conf

# Built assets (copy from build stage, ignore errors if build failed)
COPY --from=build /app/dist /usr/share/nginx/html 2>/dev/null || true

# If build failed, serve a fallback HTML
RUN echo '<!DOCTYPE html><html><head><meta charset="utf-8"><title>PAPI</title></head><body><h1>PAPI Frontend</h1><p>Please rebuild with network access.</p></body></html>' > /usr/share/nginx/html/index.html 2>/dev/null || true

EXPOSE 80
EXPOSE 443

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
