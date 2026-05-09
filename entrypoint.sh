#!/bin/sh

echo "Waiting 10 seconds for database to be ready..."
sleep 10

echo "Applying migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
python manage.py runserver 0.0.0.0:8000