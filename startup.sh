#!/bin/bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn arac_talep_sistemi.wsgi:application --bind 0.0.0.0:8000
python manage.py createsuperuser --noinput --username admin --email admin@example.com

