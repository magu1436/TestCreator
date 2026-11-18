"""デモ機能の検証専用設定。本番のDB選択には使用しない。"""
import sys
from unittest.mock import patch

# DB設定を要求しない既存の静的収集経路で共通設定を読み込む。
with patch.object(sys, "argv", ["manage.py", "collectstatic"]):
    from .settings import *  # noqa: F403

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
ALLOWED_HOSTS = ["testserver", "localhost"]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
DEMO_MODE = True
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'demo.apps.DemoConfig']
INSTALLED_APPS.append('demo.apps.DemoConfig')
DEMO_USERNAME = "demo"
DEMO_PASSWORD = "test-demo-password"
