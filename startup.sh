#!/bin/bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn projeadi.wsgi:application --bind 0.0.0.0:8000
