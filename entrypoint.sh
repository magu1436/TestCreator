#!/bin/sh
set -eu
python manage.py migrate --noinput
python manage.py initialize_runtime
exec gunicorn TestCreator.wsgi:application \
    --bind "0.0.0.0:${PORT:-8080}" --workers 2 --threads 4 --timeout 120
