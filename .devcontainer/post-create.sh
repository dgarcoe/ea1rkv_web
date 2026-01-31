#!/bin/bash
# Post-create script for GitHub Codespaces / Dev Containers

set -e

echo "=== EA1RKV Development Environment Setup ==="

# Install dependencies (in case the volume mount overwrote them)
echo "Installing Python dependencies..."
pip install --no-cache-dir -r requirements/dev.txt

# Wait for database to be ready (with timeout)
echo "Waiting for database..."
MAX_RETRIES=30
RETRY_COUNT=0

until pg_isready -h db -p 5432 -U ea1rkv -q 2>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; then
        echo "ERROR: Database not ready after ${MAX_RETRIES} seconds. Aborting."
        echo "Check that the 'db' service is running: docker compose ps"
        exit 1
    fi
    echo "  Waiting for PostgreSQL... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 1
done
echo "Database is ready."

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if it doesn't exist
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
echo "  Start server:  python manage.py runserver 0.0.0.0:8000"
echo "  Admin panel:   http://localhost:8000/admin/"
echo "  Login:         admin / admin"
echo ""
