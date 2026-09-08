#!/bin/bash
# Post-create script for GitHub Codespaces / Dev Containers
# Runs once when the container is first created.
# Uses SQLite — no Docker or PostgreSQL needed.

set -e

echo "=== EA1RKV Development Environment Setup ==="

# --- System dependencies for Pillow (image processing) ---
echo "Installing system dependencies..."
sudo apt-get update && sudo apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    && sudo rm -rf /var/lib/apt/lists/*

# --- Python dependencies ---
echo "Installing Python dependencies..."
pip install --no-cache-dir -r requirements/dev.txt

# --- Django setup ---
echo "Running migrations..."
python manage.py migrate --noinput
python manage.py setup_radioclub

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create dev superuser
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
echo "  Start the server with: python manage.py runserver 0.0.0.0:8000"
echo "  Admin panel: http://localhost:8000/admin/"
echo "  Login:       admin / admin"
echo ""

