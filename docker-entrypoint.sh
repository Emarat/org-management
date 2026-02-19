#!/bin/sh
set -e

echo "Starting docker entrypoint..."

# Wait for Postgres if configured
if [ -n "$POSTGRES_HOST" ]; then
  echo "Waiting for Postgres at $POSTGRES_HOST:${POSTGRES_PORT:-5432}..."
  if command -v pg_isready >/dev/null 2>&1; then
    until pg_isready -h "$POSTGRES_HOST" -p "${POSTGRES_PORT:-5432}" >/dev/null 2>&1; do
      sleep 1
    done
  else
    sleep 3
  fi
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

echo "Executing command: $@"
exec "$@"
