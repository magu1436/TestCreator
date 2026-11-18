"""DBへ接続しない子プロセスで起動前の設定検証を確認する。"""
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase


class DemoStartupTests(TestCase):
    def run_command(self, engine, *, mode=True, password='test-password',
                    username='demo', command='migrate'):
        with TemporaryDirectory() as directory:
            app_settings = ('' if mode else
                'INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "demo.apps.DemoConfig"]\n')
            Path(directory, 'isolated_demo.py').write_text(
                'from TestCreator.demo_test_settings import *\n'
                f'DEMO_MODE = {mode!r}\nDEMO_PASSWORD = {password!r}\n'
                f'DEMO_USERNAME = {username!r}\n'
                + app_settings +
                f'DATABASES = {{"default": {{"ENGINE": {engine!r}, "NAME": ":memory:"}}}}\n'
                'STATIC_ROOT = "/tmp/testcreator-demo-static"\n', encoding='utf-8')
            env = os.environ | {'PYTHONPATH': directory + os.pathsep + str(Path.cwd()),
                                'OPENAI_API_KEY': 'test-only', 'API_KEY': 'test-only'}
            return subprocess.run([sys.executable, 'manage.py', command, '--noinput',
                                   '--settings=isolated_demo'], env=env, capture_output=True, timeout=30)

    def test_migrate_refuses_normal_database_before_connection(self):
        for engine in ('django.db.backends.mysql', 'django_tidb'):
            with self.subTest(engine=engine):
                result = self.run_command(engine)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('SQLite', result.stderr.decode())
                self.assertNotIn('OperationalError', result.stderr.decode())

    def test_sqlite_migration_is_accepted_and_password_is_required(self):
        self.assertEqual(self.run_command('django.db.backends.sqlite3').returncode, 0)
        result = self.run_command('django.db.backends.sqlite3', password='')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DEMO_PASSWORD', result.stderr.decode())

    def test_collectstatic_needs_neither_database_nor_demo_password(self):
        for mode in (False, True):
            with self.subTest(mode=mode):
                result = self.run_command('django.db.backends.dummy', mode=mode,
                                          password='', command='collectstatic')
                self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_collectstatic_does_not_validate_username_credentials(self):
        for username in (' demo ', 'ｄｅｍｏ'):
            with self.subTest(username=username):
                result = self.run_command('django.db.backends.dummy', password='',
                                          username=username, command='collectstatic')
                self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_normal_mode_does_not_require_demo_credentials(self):
        self.assertEqual(self.run_command('django.db.backends.sqlite3', mode=False, password='').returncode, 0)
