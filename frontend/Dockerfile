# Build Stage
FROM node:22-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Production Stage with Nginx
FROM nginx:1.25-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE $PORT

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD sh -c "wget --quiet --tries=1 --spider http://localhost:\$PORT/ || exit 1"

CMD ["nginx", "-g", "daemon off;"]
