#!/bin/sh
set -e

echo "Starting docker entrypoint..."

# If Postgres is used, wait for it to be ready
if [ -n "$POSTGRES_HOST" ]; then
  echo "Waiting for Postgres at $POSTGRES_HOST:$POSTGRES_PORT..."
  # Use pg_isready if available
  if command -v pg_isready >/dev/null 2>&1; then
    until pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT:-5432}" >/dev/null 2>&1; do
      sleep 1
    done
  else
    # fallback: simple sleep to give DB time to start
    sleep 3
  fi
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

echo "Starting Gunicorn..."
exec gunicorn org_management.wsgi:application --bind 0.0.0.0:8000 --workers 3
