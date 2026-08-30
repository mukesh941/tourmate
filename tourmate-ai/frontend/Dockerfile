# Build stage
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json .
RUN npm ci --omit=dev
COPY . .
RUN npm run build

# Runtime stage
FROM node:20-slim
WORKDIR /app
RUN useradd -m -u 1000 appuser && apt-get update && apt-get install -y --no-install-recommends nginx && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
RUN chown -R appuser:appuser /var/log/nginx /var/cache/nginx
USER appuser
EXPOSE 5173
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:5173 || exit 1
CMD ["nginx", "-g", "daemon off;"]
