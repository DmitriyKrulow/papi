# PAPI frontend image (multi-stage: build with Node, serve with nginx)

# ---- Build stage ----
FROM node:22-alpine AS build

WORKDIR /app

# Install dependencies (uses lockfile for reproducibility)
COPY package.json package-lock.json ./
RUN npm ci

# Copy source and build static assets
COPY . .
RUN npm run build

# ---- Serve stage ----
FROM nginx:1.27-alpine

# Install certbot, openssl, and envsubst for SSL management
RUN apk add --no-cache certbot openssl gettext

# SPA + reverse-proxy config for the backend (HTTP only)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Built assets
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
EXPOSE 443

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
