#!/bin/bash
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn arac_talep_sistemi.wsgi:application
