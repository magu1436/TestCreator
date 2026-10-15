FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    default-mysql-client \
    pkg-config \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    libjpeg62-turbo \
    libopenjp2-7 \
    fonts-noto-cjk \
    util-linux \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv \
    && chown -R vscode:vscode /opt/venv

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TESTCREATOR_DEVCONTAINER=1

# Preserve a writable mount point when Docker creates the node_modules volume.
RUN mkdir -p /workspaces/TestCreator/node_modules \
    && chown -R vscode:vscode /workspaces
