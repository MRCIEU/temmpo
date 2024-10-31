#!/bin/bash
set -e

# Collect static files
python3 manage.py collectstatic --no-input

# Run database migrations
python3 manage.py migrate

# Run Django development server
python3 manage.py runserver $DJANGO_HOST:$DJANGO_PORT