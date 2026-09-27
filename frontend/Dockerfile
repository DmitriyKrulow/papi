# PAPI frontend image (multi-stage: build with Node, serve with nginx)

# ---- Build stage ----
FROM node:22-alpine AS build

WORKDIR /app

# Configure npm mirror for regions with restricted npm registry access
RUN npm config set registry https://registry.npmmirror.com

# Install dependencies (uses lockfile for reproducibility)
COPY package.json package-lock.json ./
RUN npm ci

# Copy source and build static assets
COPY . .
RUN npm run build

# ---- Serve stage ----
FROM nginx:1.27-alpine

# Configure Alpine mirror for regions with restricted access
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories 2>/dev/null || true

# Install certbot, openssl, and envsubst for SSL management
RUN apk add --no-cache certbot openssl gettext

# Copy HTTP config (used as fallback when SSL is not available)
COPY nginx-http.conf /etc/nginx/nginx-http.conf

# Built assets
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
EXPOSE 443

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
