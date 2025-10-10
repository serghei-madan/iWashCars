web: gunicorn iwashcars.wsgi:application --bind 0.0.0.0:${PORT} --workers 3
worker: python manage.py qcluster
release: python manage.py migrate --noinput
