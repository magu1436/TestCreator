#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

python -m pip install -r requirements.txt
npm ci
npm run build
python manage.py check --database default
python manage.py migrate --noinput
python manage.py ensure_superuser
