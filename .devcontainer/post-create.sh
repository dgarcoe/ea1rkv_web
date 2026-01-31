#!/bin/bash
# Post-create script for GitHub Codespaces / Dev Containers

set -e

echo "=== EA1RKV Development Environment Setup ==="

# Wait for database to be ready
echo "Waiting for database..."
while ! python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(('db', 5432))
    s.close()
    exit(0)
except:
    exit(1)
" 2>/dev/null; do
    sleep 1
done
echo "Database is ready."

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

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
echo "  Site:  http://localhost:8000/"
echo "  Admin: http://localhost:8000/admin/"
echo "  Login: admin / admin"
echo ""
