#!/bin/sh
# Entrypoint script for Django-Q worker

echo "Waiting for database to be ready..."
python -c "
import os
import time
import dj_database_url
import psycopg2
from psycopg2 import OperationalError

db_url = os.getenv('DATABASE_URL')
if not db_url:
    print('ERROR: DATABASE_URL not set!')
    exit(1)

db_config = dj_database_url.parse(db_url)
max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        conn = psycopg2.connect(
            dbname=db_config['NAME'],
            user=db_config['USER'],
            password=db_config['PASSWORD'],
            host=db_config['HOST'],
            port=db_config['PORT']
        )
        conn.close()
        print('Database is ready!')
        break
    except OperationalError:
        retry_count += 1
        print(f'Database not ready yet, retrying ({retry_count}/{max_retries})...')
        time.sleep(2)

if retry_count >= max_retries:
    print('ERROR: Could not connect to database after maximum retries')
    exit(1)
"

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Starting Django-Q cluster..."
exec python manage.py qcluster
