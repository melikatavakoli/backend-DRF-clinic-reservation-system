#!/bin/sh

echo "Waiting 10 seconds for database to be ready..."
sleep 10

echo "Applying migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
daphne -b 0.0.0.0 -p 8000 config.asgi:application