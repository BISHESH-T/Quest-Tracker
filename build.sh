#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --no-cache-dir --force-reinstall -r requirements.txt
mkdir -p media
rm -rf staticfiles

python manage.py collectstatic --no-input --clear
python manage.py migrate