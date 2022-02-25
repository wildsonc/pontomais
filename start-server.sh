#!/bin/bash
  
# turn on bash's job control
set -m

celery -A core worker --autoscale 1,16 --detach &&
celery -A core beat -S django_celery_beat.schedulers:DatabaseScheduler -l DEBUG --detach &&
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --access-logfile - --workers 3