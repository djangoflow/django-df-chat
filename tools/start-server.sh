#!/bin/sh

set -e

. ./venv/bin/activate
docker-compose up -d
python manage.py migrate
python manage.py runserver
