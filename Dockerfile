# Multi-stage Docker build for iWashCars Django application

# Stage 1: Builder - Install dependencies
FROM python:3.10-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies needed for Python packages and Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy package.json and install Node dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy static files and build CSS
COPY static ./static
RUN npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify

# Stage 2: Runtime - Create production image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security (non-root)
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /app/staticfiles /app/media && \
    chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy entrypoint scripts and make them executable
COPY entrypoint.sh worker-entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh /app/worker-entrypoint.sh && \
    chown appuser:appuser /app/entrypoint.sh /app/worker-entrypoint.sh

# Copy application code (excluding input.css which is only needed for build)
COPY --chown=appuser:appuser . .

# Remove input.css from static directory (we only need output.css)
RUN rm -f /app/static/css/input.css

# Copy built CSS from builder stage
COPY --from=builder --chown=appuser:appuser /app/static/css/output.css /app/static/css/output.css

# Switch to non-root user
USER appuser

# Collect static files
RUN python manage.py collectstatic --noinput --clear

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000', timeout=5)" || exit 1

# Run gunicorn via entrypoint script
CMD ["/app/entrypoint.sh"]
