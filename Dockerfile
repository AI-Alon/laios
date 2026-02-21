# ============================================================================
# Stage 1: Build React frontend
# ============================================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/web

# Install dependencies first (layer cache)
COPY web/package.json web/package-lock.json* ./
RUN npm ci --silent

# Build the app
COPY web/ ./
RUN npm run build


# ============================================================================
# Stage 2: Python runtime
# ============================================================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install system dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python package
COPY pyproject.toml ./
COPY laios/ ./laios/
COPY config/ ./config/
RUN pip install --no-cache-dir -e ".[api,llm]"

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/web/dist ./web/dist

# Create data directory (will be mounted as a volume)
RUN mkdir -p /root/.laios/logs /root/.laios/memory /root/.laios/sessions /root/.laios/plugins

EXPOSE 8000

# Healthcheck — uses the public /api/health endpoint (no auth required)
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["laios", "serve", "--host", "0.0.0.0", "--port", "8000"]
