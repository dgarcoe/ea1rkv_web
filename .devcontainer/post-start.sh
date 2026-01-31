#!/bin/bash
# Post-start script for GitHub Codespaces / Dev Containers
# Runs every time the container starts (including restarts).

set -e

# Ensure PostgreSQL is running (survives Codespace stop/start)
echo "Ensuring PostgreSQL is running..."
docker compose up -d db

# Wait briefly for database
until pg_isready -h localhost -p 5432 -U ea1rkv -q 2>/dev/null; do
    sleep 1
done

# Start Django development server in background
echo "Starting development server on port 8000..."
nohup python manage.py runserver 0.0.0.0:8000 > /tmp/django-server.log 2>&1 &

echo "Dev server started. Logs at /tmp/django-server.log"
