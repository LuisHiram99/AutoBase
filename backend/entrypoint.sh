#!/bin/sh
set -e

echo "Starting backend..."

# Wait for database to be available (optional health check)
if [ -n "$DATABASE_URL" ]; then
    echo "Checking database connection..."
    # Ensure DATABASE_URL uses asyncpg driver
    if echo "$DATABASE_URL" | grep -q "^postgres://"; then
        export DATABASE_URL=$(echo "$DATABASE_URL" | sed 's|^postgres://|postgresql+asyncpg://|')
    elif echo "$DATABASE_URL" | grep -q "^postgresql://"; then
        export DATABASE_URL=$(echo "$DATABASE_URL" | sed 's|^postgresql://|postgresql+asyncpg://|')
    fi
    echo "Using DATABASE_URL with asyncpg driver"
fi

echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI application..."
# Use PORT environment variable provided by Railway
exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1