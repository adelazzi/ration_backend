#!/usr/bin/env bash
# Render build step: install, collect static files, apply migrations.
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Optional first admin: set DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL and
# DJANGO_SUPERUSER_PASSWORD on Render once, deploy, then remove them.
if [[ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]]; then
  python manage.py createsuperuser --no-input || echo "Superuser already exists, skipping."
fi
