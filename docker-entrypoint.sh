#!/bin/sh
set -e

echo "Starting docker entrypoint..."

if [ -n "$POSTGRES_HOST" ]; then
  echo "Waiting for Postgres at $POSTGRES_HOST:${POSTGRES_PORT:-5432}..."
  until pg_isready -h "$POSTGRES_HOST" -p "${POSTGRES_PORT:-5432}" >/dev/null 2>&1; do
    sleep 1
  done
fi

# Run one-time tasks
echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn org_management.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3
