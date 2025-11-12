#!/bin/bash

# Exit on error
set -e

echo "Waiting for PostgreSQL to be ready..."
while ! nc -z postgres 5432; do
  sleep 0.5
done
echo "PostgreSQL is ready!"

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Starting application..."
exec "$@"
