#!/bin/bash
set -e

# Wait for the database to be ready
echo "Waiting for database..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done
echo "Database is ready!"

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting application..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} 
