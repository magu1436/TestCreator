FROM python:3.12-slim-bookworm AS dependencies
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 ca-certificates \
    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
    libjpeg62-turbo libopenjp2-7 fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=TestCreator.production \
    PORT=8080
WORKDIR /app
COPY --from=dependencies /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels
COPY . .
RUN python manage.py collectstatic --noinput
CMD ["/bin/sh", "/app/entrypoint.sh"]
