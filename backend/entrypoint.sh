#!/bin/sh
set -e

echo "Starting backend..."

# Wait for database to be available (optional health check)
if [ -n "$DATABASE_URL" ]; then
    echo "Checking database connection..."
    # Simple connection test - modify as needed for your setup
fi

echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI application..."
# Use PORT environment variable provided by Railway
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1