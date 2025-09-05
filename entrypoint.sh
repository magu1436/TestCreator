#!/bin/sh
set -e

echo "[entrypoint] running migrate..."
python manage.py migrate --noinput

# 環境変数があれば superuser を作成（既にあればスキップ）
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  echo "[entrypoint] ensuring superuser..."
  # manage.py shell 経由で Django を初期化してから実行
  python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
u = (os.environ.get('DJANGO_SUPERUSER_USERNAME') or '').replace('\ufeff','').strip()
p = (os.environ.get('DJANGO_SUPERUSER_PASSWORD') or '').replace('\ufeff','').strip()
if u and p:
    if not User.objects.filter(username=u).exists():
        User.objects.create_superuser(u, p)
        print(f'Created superuser: {u}')
    else:
        print(f'Superuser already exists: {u}')
else:
    print('Superuser env not set; skip')
"
fi

echo "[entrypoint] starting gunicorn..."
exec gunicorn TestCreator.wsgi:application \
  --bind 0.0.0.0:$PORT \
  --workers 2 \
  --threads 4 \
  --timeout 120