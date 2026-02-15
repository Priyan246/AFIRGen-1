# Multi-stage build for AFIRGen Frontend
# Supports configurable API URL via build arguments

FROM nginx:alpine

# Build arguments for configuration
ARG API_BASE_URL=http://localhost:8000
ARG ENVIRONMENT=production
ARG ENABLE_DEBUG=false

# Copy frontend files
COPY base.html /usr/share/nginx/html/index.html
COPY style.css /usr/share/nginx/html/
COPY script.js /usr/share/nginx/html/
COPY config.js /usr/share/nginx/html/

# Configure API URL at build time
RUN sed -i "s|API_BASE_URL: '[^']*'|API_BASE_URL: '${API_BASE_URL}'|g" /usr/share/nginx/html/config.js && \
    sed -i "s|ENVIRONMENT: '[^']*'|ENVIRONMENT: '${ENVIRONMENT}'|g" /usr/share/nginx/html/config.js && \
    sed -i "s|ENABLE_DEBUG: [^,]*,|ENABLE_DEBUG: ${ENABLE_DEBUG},|g" /usr/share/nginx/html/config.js

# Add custom nginx configuration for SPA routing
RUN echo 'server { \
    listen 80; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    # Security headers \
    add_header X-Frame-Options "SAMEORIGIN" always; \
    add_header X-Content-Type-Options "nosniff" always; \
    add_header X-XSS-Protection "1; mode=block" always; \
    \
    # Gzip compression \
    gzip on; \
    gzip_vary on; \
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript; \
    \
    # Cache static assets \
    location ~* \.(css|js|jpg|jpeg|png|gif|ico|svg|woff|woff2|ttf|eot)$ { \
        expires 1y; \
        add_header Cache-Control "public, immutable"; \
    } \
    \
    # No cache for HTML \
    location ~* \.html$ { \
        expires -1; \
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"; \
    } \
    \
    # SPA fallback \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
