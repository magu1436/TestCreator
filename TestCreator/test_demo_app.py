"""隔離プロセスでデモ専用アプリと通常スキーマの境界を検証する。"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase


class DemoAppTests(TestCase):
    def environment(self, root):
        env = {key: value for key, value in os.environ.items()
               if not key.startswith(('DEMO_', 'DB_', 'PYTHON', 'DJANGO_'))}
        env.update(PYTHONPATH=str(root) + os.pathsep + str(Path.cwd()),
                   DJANGO_SETTINGS_MODULE='isolated_app', OPENAI_API_KEY='test-only',
                   DB_BACKEND='mysql', DB_HOST='must-not-connect.invalid', DB_PORT='3306',
                   DB_NAME='unused', DB_USER='unused', DB_PASSWORD='unused')
        return env

    def configure(self, root, *, mode, registered=None):
        body = ('from TestCreator.settings import *\n'
                f'DEMO_MODE = {mode!r}\nDEMO_PASSWORD = "test-only"\n'
                f'DATABASES = {{"default": {{"ENGINE": "django.db.backends.sqlite3", "NAME": {str(root / "isolated.sqlite3")!r}}}}}\n')
        if registered is not None:
            body += 'INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "demo.apps.DemoConfig"]\n'
            if registered:
                body += 'INSTALLED_APPS += ["demo.apps.DemoConfig"]\n'
        (root / 'isolated_app.py').write_text(body, encoding='utf-8')
        env = self.environment(root)
        env['DEMO_MODE'] = str(mode).lower()
        return env

    def run_python(self, env, code):
        return subprocess.run([sys.executable, '-c', code], env=env,
                              capture_output=True, timeout=30)

    def test_normal_mode_has_no_demo_schema(self):
        with TemporaryDirectory() as directory:
            env = self.configure(Path(directory), mode=False)
            result = self.run_python(env, '''
import django; django.setup()
from django.apps import apps
from django.core.management import call_command
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.test.utils import CaptureQueriesContext
from django.core.management.base import CommandError
assert not apps.is_installed('demo')
call_command('migrate', interactive=False, verbosity=0)
assert not {'home_demoinitialization', 'demo_demoinitialization'} & set(connection.introspection.table_names())
assert not any(app in ('demo', 'home') for app, name in MigrationLoader(connection).graph.nodes)
assert not ContentType.objects.filter(model='demoinitialization').exists()
assert not Permission.objects.filter(content_type__model='demoinitialization').exists()
call_command('makemigrations', check=True, dry_run=True, verbosity=0)
with CaptureQueriesContext(connection) as queries:
    try:
        call_command('seed_demo', verbosity=0)
    except CommandError:
        pass
    else:
        raise AssertionError('通常モードの投入を拒否しませんでした')
assert len(queries) == 0
import os
from django.contrib.auth import get_user_model
os.environ['DJANGO_SUPERUSER_USERNAME'] = 'normal-admin'
os.environ['DJANGO_SUPERUSER_PASSWORD'] = 'normal-only-password'
call_command('initialize_runtime', verbosity=0)
user = get_user_model().objects.get(username='normal-admin')
assert user.is_active and user.is_staff and user.is_superuser
assert user.check_password('normal-only-password')
''')
            self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_demo_mode_uses_demo_app_schema(self):
        with TemporaryDirectory() as directory:
            env = self.configure(Path(directory), mode=True)
            result = self.run_python(env, '''
import django; django.setup()
from django.apps import apps
from django.core.management import call_command
from django.db import connection
assert apps.is_installed('demo')
marker = apps.get_model('demo', 'DemoInitialization')
assert marker._meta.db_table == 'demo_demoinitialization'
call_command('migrate', interactive=False, verbosity=0)
assert 'demo_demoinitialization' in connection.introspection.table_names()
assert 'home_demoinitialization' not in connection.introspection.table_names()
call_command('makemigrations', check=True, dry_run=True, verbosity=0)
''')
            self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_noncanonical_username_is_rejected_before_database_creation(self):
        for username in (' demo ', 'ｄｅｍｏ', 'a' * 151, 'invalid\x00name'):
            with self.subTest(username=username), TemporaryDirectory() as directory:
                root = Path(directory)
                env = self.configure(root, mode=True)
                with (root / 'isolated_app.py').open('a', encoding='utf-8') as config:
                    config.write(f'DEMO_USERNAME = {username!r}\n')
                result = self.run_python(env, 'import django; django.setup(); '
                    'from django.core.management import call_command; '
                    'call_command("migrate", interactive=False, verbosity=0)')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('DEMO_USERNAMEは前後の空白がなく、NFKC正規化済み', result.stderr.decode())
                self.assertFalse((root / 'isolated.sqlite3').exists())

    def test_normal_mode_cannot_retain_reserved_demo_database(self):
        for restore_database in (False, True):
            with self.subTest(restore_database=restore_database), TemporaryDirectory() as directory:
                root = Path(directory)
                body = ('from TestCreator.production import *\n'
                        'DEMO_MODE = False\n'
                        'INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "demo.apps.DemoConfig"]\n')
                if restore_database:
                    body += ('DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", '
                             f'"NAME": {str(root / "normal.sqlite3")!r}}}}}\n')
                (root / 'isolated_app.py').write_text(body, encoding='utf-8')
                env = self.environment(root)
                env.update(DEMO_MODE='true', DEMO_PASSWORD='test-only', TMPDIR=str(root))
                result = self.run_python(env, 'import django; django.setup(); '
                    'from django.core.management import call_command; '
                    'call_command("migrate", interactive=False, verbosity=0)')
                if restore_database:
                    self.assertEqual(result.returncode, 0, result.stderr.decode())
                    self.assertTrue((root / 'normal.sqlite3').exists())
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('通常モードではデモ専用DBを使用できません', result.stderr.decode())
                    self.assertNotIn('OperationalError', result.stderr.decode())
                    static_result = self.run_python(env,
                        'import isolated_app; import sys; sys.argv=["manage.py", "collectstatic"]; '
                        'import django; django.setup(); '
                        'from django.core.management import call_command; '
                        'call_command("collectstatic", interactive=False, verbosity=0)')
                    self.assertEqual(static_result.returncode, 0, static_result.stderr.decode())
                self.assertFalse((root / 'testcreator-demo.sqlite3').exists())

    def test_mismatched_mode_and_app_fails_before_migration(self):
        for mode, registered in ((True, False), (False, True)):
            for command in ('migrate', 'collectstatic'):
                with self.subTest(mode=mode, registered=registered, command=command), TemporaryDirectory() as directory:
                    root = Path(directory)
                    env = self.configure(root, mode=mode, registered=registered)
                    result = self.run_python(env, 'import sys; '
                        f'sys.argv=["manage.py", {command!r}]; '
                        'import django; django.setup(); '
                        'from django.core.management import call_command; '
                        f'call_command({command!r}, interactive=False, verbosity=0)')
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('DEMO_MODEとdemoアプリ', result.stderr.decode())
                    self.assertNotIn('OperationalError', result.stderr.decode())
                    self.assertFalse((root / 'isolated.sqlite3').exists())

    def test_dotenv_and_environment_choose_installed_apps(self):
        for process_mode, expected in ((None, True), ('false', False), ('true', True)):
            with self.subTest(process_mode=process_mode), TemporaryDirectory() as directory:
                root = Path(directory)
                package = root / 'TestCreator'
                package.mkdir()
                for name in ('__init__.py', 'settings.py', 'database.py', 'demo.py'):
                    shutil.copyfile(Path(__file__).with_name(name), package / name)
                (root / '.env').write_text('DEMO_MODE=true\nDEMO_PASSWORD=test-only\n', encoding='utf-8')
                env = self.environment(root)
                env['DJANGO_SETTINGS_MODULE'] = 'TestCreator.settings'
                if process_mode is not None:
                    env['DEMO_MODE'] = process_mode
                result = subprocess.run([sys.executable, '-c',
                    'import django; django.setup(); from django.apps import apps; '
                    'from django.conf import settings; '
                    f'assert settings.DEMO_MODE is {expected!r}; '
                    f'assert apps.is_installed("demo") is {expected!r}'],
                    cwd=root, env=env, capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr.decode())
