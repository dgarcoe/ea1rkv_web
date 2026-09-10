#!/bin/sh
set -eu

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files into the shared volume..."
python manage.py collectstatic --noinput

exec "$@"
