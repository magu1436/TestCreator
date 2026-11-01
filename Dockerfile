FROM node:22-bookworm-slim AS static-build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY tsconfig.json tsconfig.base.json ./
COPY static/shared/ ./static/shared/
COPY vocab/tsconfig.json ./vocab/tsconfig.json
COPY vocab/static/vocab/js/src/ ./vocab/static/vocab/js/src/
COPY ocr/tsconfig.json ./ocr/tsconfig.json
COPY ocr/static/ocr/js/src/ ./ocr/static/ocr/js/src/
COPY quiz/tsconfig.json ./quiz/tsconfig.json
COPY quiz/static/quiz/js/src/ ./quiz/static/quiz/js/src/
RUN npm run build

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
COPY --from=static-build /app/static/shared/dist/ ./static/shared/dist/
COPY --from=static-build /app/vocab/static/vocab/js/dist/ ./vocab/static/vocab/js/dist/
COPY --from=static-build /app/ocr/static/ocr/js/dist/ ./ocr/static/ocr/js/dist/
COPY --from=static-build /app/quiz/static/quiz/js/dist/ ./quiz/static/quiz/js/dist/
RUN python manage.py collectstatic --noinput
CMD ["/bin/sh", "/app/entrypoint.sh"]
