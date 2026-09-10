#!/bin/sh
set -eu

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Ensuring the radioclub page tree exists..."
python manage.py setup_radioclub

echo "Collecting static files into the shared volume..."
python manage.py collectstatic --noinput

exec "$@"
