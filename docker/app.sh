#!/bin/bash

set -e

echo "Run migrations..."
alembic upgrade head
echo "Migrations created"

echo "Start gunicorn..."
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000
echo "Gunicorn started"

exec "$@"
