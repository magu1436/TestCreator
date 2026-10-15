#!/usr/bin/env bash
set -euo pipefail
cd /workspaces/TestCreator

# Named volumes may be owned by root on their first use.
sudo chown "$(id -u):$(id -g)" node_modules
python -m pip install -r requirements.txt
npm ci
npm run build
python manage.py check --database default
