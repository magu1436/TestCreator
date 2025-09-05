# Pythonの軽量ベース
FROM python:3.12-slim

# WeasyPrint が必要とする OS ライブラリ
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libharfbuzz0b \
    libffi8 \
    libjpeg62-turbo \
    libpng16-16 \
    shared-mime-info \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 環境
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# 作業ディレクトリ
WORKDIR /app

# 依存インストール
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# ソース一式をコピー
COPY . /app

# Static をビルド時に収集（WhiteNoise配布）
RUN python manage.py collectstatic --noinput

# Gunicorn で起動
# 例: プロジェクト名は TestCreator
CMD ["gunicorn", "TestCreator.wsgi:application", "--bind", "0.0.0.0:${PORT}", "--workers", "2", "--threads", "4", "--timeout", "120"]