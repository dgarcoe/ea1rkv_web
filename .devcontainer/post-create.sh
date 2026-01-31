#!/bin/bash
# Post-create script for GitHub Codespaces / Dev Containers
# Runs once when the container is first created.

set -e

echo "=== EA1RKV Development Environment Setup ==="

# --- System dependencies ---
echo "Installing system dependencies..."
sudo apt-get update && sudo apt-get install -y --no-install-recommends \
    libpq-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    postgresql-client \
    && sudo rm -rf /var/lib/apt/lists/*

# --- Python dependencies ---
echo "Installing Python dependencies..."
pip install --no-cache-dir -r requirements/dev.txt

# --- Start PostgreSQL via Docker ---
echo "Starting PostgreSQL container..."
docker compose up -d db

# Wait for database to be ready (with timeout)
echo "Waiting for database..."
MAX_RETRIES=30
RETRY_COUNT=0

until pg_isready -h localhost -p 5432 -U ea1rkv -q 2>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; then
        echo "ERROR: Database not ready after ${MAX_RETRIES} seconds."
        echo "Try manually: docker compose up -d db"
        exit 1
    fi
    echo "  Waiting for PostgreSQL... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 1
done
echo "Database is ready."

# --- Django setup ---
echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create dev superuser if it doesn't exist
echo "Creating superuser (admin/admin)..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@ea1rkv.es', 'admin')
    print('Superuser created: admin / admin')
else:
    print('Superuser already exists.')
"

echo ""
echo "=== Setup Complete ==="
echo "  The dev server will start automatically."
echo "  Admin panel: http://localhost:8000/admin/"
echo "  Login:       admin / admin"
echo ""
