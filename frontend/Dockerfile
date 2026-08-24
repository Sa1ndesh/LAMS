# =====================================================================
# LAMS Frontend Production Dockerfile (Multi-stage Build)
# Stage 1: Build Vite React Static Assets
# Stage 2: Production Nginx Server
# =====================================================================

# ----- Stage 1: Build Environment -----
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests
COPY package.json package-lock.json ./

# Install npm dependencies
RUN npm ci

# Copy application source code
COPY . .

# Build argument for configurable public API URL
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build production bundle with TypeScript check
RUN npm run build

# ----- Stage 2: Production Web Server -----
FROM nginx:alpine AS runner

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose HTTP port 80
EXPOSE 80

# Health check for Nginx server
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

