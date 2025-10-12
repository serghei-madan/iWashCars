#!/bin/sh
# Entrypoint script for iWashCars Docker container

# Set default PORT if not provided
PORT=${PORT:-8000}

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Starting gunicorn on port ${PORT}..."

# Run gunicorn with environment-based PORT
exec gunicorn iwashcars.wsgi:application \
    --bind "0.0.0.0:${PORT}" \
    --workers 3 \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
