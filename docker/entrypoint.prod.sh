#!/bin/sh
set -eu

# Initialize mounted volume roots, then permanently drop privileges.
if [ "$(id -u)" = "0" ]; then
    mkdir -p /app/media /app/staticfiles
    chown app:app /app/media /app/staticfiles
    exec gosu app:app "$0" "$@"
fi

if [ ! -w /app/media ] || [ ! -w /app/staticfiles ]; then
    echo "Media/static volumes must be writable by app." >&2
    exit 1
fi

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Ensuring the radioclub page tree exists..."
python manage.py setup_radioclub

echo "Collecting static files into the shared volume..."
python manage.py collectstatic --noinput

exec "$@"
