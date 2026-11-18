"""共有ユーザーと公開サンプルの初回初期化を検証する。"""
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
from tempfile import TemporaryDirectory
from unittest import TestCase as ProcessTestCase
from unittest.mock import patch

from django.apps import apps
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from accounts.forms import LoginForm
from vocab.models import Word
from wordbank.models import WordList


class DemoInitializationTests(TestCase):
    @property
    def marker(self):
        return apps.get_model('demo', 'DemoInitialization')

    def initialize(self):
        call_command('ensure_demo_user', stdout=StringIO())
        call_command('seed_demo', stdout=StringIO())

    def test_runtime_stops_on_user_or_seed_failure(self):
        for failing in ('ensure_demo_user', 'seed_demo'):
            calls = []

            def dispatch(name):
                calls.append(name)
                if name == failing:
                    raise CommandError('initialization failed')

            with patch('accounts.management.commands.initialize_runtime.call_command', dispatch):
                with self.assertRaises(CommandError):
                    call_command('initialize_runtime')
            self.assertEqual(calls, ['ensure_demo_user'] if failing == 'ensure_demo_user'
                             else ['ensure_demo_user', 'seed_demo'])
        with override_settings(DEMO_MODE=False):
            with patch('accounts.management.commands.initialize_runtime.call_command',
                       side_effect=CommandError('initialization failed')) as dispatch:
                with self.assertRaises(CommandError):
                    call_command('initialize_runtime')
                dispatch.assert_called_once_with('ensure_superuser')

    def test_repeat_keeps_edits_deletions_and_password_hash(self):
        self.initialize()
        user = get_user_model().objects.get(username='demo')
        password = user.password
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff or user.is_superuser)
        self.assertEqual(authenticate(username='demo', password='test-demo-password'), user)
        form = LoginForm(data={'username': 'demo', 'password': 'test-demo-password'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.get_user(), user)
        for username in (' demo ', 'ｄｅｍｏ'):
            self.assertEqual(form.fields['username'].clean(username), 'demo')
        self.assertEqual(Word.objects.count(), 70)
        self.assertEqual(list(WordList.objects.order_by('pk').values_list('name', flat=True)),
                         ['デモ英単語50', 'デモ古文単語20'])
        self.assertFalse(WordList.objects.exclude(created_by=user).exists())
        self.assertFalse(Word.objects.exclude(latest_edited_by=user).exists())
        samples = json.loads((Path(__file__).resolve().parent.parent / 'demo' / 'data' /
                              'samples.json').read_text(encoding='utf-8-sig'))
        for sample in samples['wordlists']:
            with self.subTest(wordlist=sample['name']):
                wordlist = WordList.objects.get(name=sample['name'])
                self.assertEqual(list(wordlist.words.order_by('number').values(
                    'number', 'term', 'meaning')), sample['words'])
        self.assertEqual(self.marker.objects.count(), 1)
        word = Word.objects.first()
        word.term = 'edited'
        word.save()
        Word.objects.exclude(pk=word.pk).first().delete()
        self.initialize()
        user.refresh_from_db()
        word.refresh_from_db()
        self.assertEqual(user.password, password)
        self.assertEqual(word.term, 'edited')
        self.assertEqual(Word.objects.count(), 69)
        self.assertEqual(WordList.objects.count(), 2)
        self.assertEqual(self.marker.objects.count(), 1)
        Word.objects.all().delete()
        WordList.objects.all().delete()
        self.initialize()
        self.assertEqual(WordList.objects.count(), 0)
        self.assertEqual(Word.objects.count(), 0)
        self.assertEqual(self.marker.objects.count(), 1)

    def test_user_privileges_and_password_are_reconciled(self):
        user = get_user_model().objects.create_superuser(username='demo', password='old')
        user.is_active = False
        user.save()
        user.groups.add(Group.objects.create(name='former-admin'))
        user.user_permissions.add(Permission.objects.first())
        self.initialize()
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff or user.is_superuser)
        self.assertFalse(user.groups.exists())
        self.assertFalse(user.user_permissions.exists())
        self.assertTrue(user.check_password('test-demo-password'))
        with override_settings(DEMO_PASSWORD='rotated'):
            self.initialize()
        user.refresh_from_db()
        self.assertTrue(user.check_password('rotated'))

    def test_seed_failure_rolls_back_and_can_retry(self):
        call_command('ensure_demo_user', stdout=StringIO())
        bulk_create = Word.objects.bulk_create
        calls = []

        def fail_second_book(words):
            calls.append(words)
            if len(calls) == 2:
                raise RuntimeError('seed failed')
            return bulk_create(words)

        with patch('vocab.models.Word.objects.bulk_create', side_effect=fail_second_book):
            with self.assertRaises(RuntimeError):
                call_command('seed_demo', stdout=StringIO())
        self.assertEqual(len(calls), 2)
        self.assertEqual(WordList.objects.count(), 0)
        self.assertEqual(Word.objects.count(), 0)
        self.assertEqual(self.marker.objects.count(), 0)
        self.initialize()
        self.assertEqual(Word.objects.count(), 70)
        self.assertEqual(self.marker.objects.count(), 1)

    @override_settings(DEMO_MODE=False)
    def test_commands_refuse_normal_mode_without_database_queries(self):
        for command in ('ensure_demo_user', 'seed_demo'):
            with self.assertNumQueries(0), self.assertRaises(CommandError):
                call_command(command, stdout=StringIO())


class DemoFileDatabaseTests(ProcessTestCase):
    def test_runtime_uses_dotenv_and_explicit_environment_precedence(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'TestCreator'
            package.mkdir()
            for name in ('__init__.py', 'settings.py', 'database.py', 'demo.py'):
                shutil.copyfile(Path(__file__).with_name(name), package / name)
            (root / '.env').write_text(
                'DEMO_MODE=true\nDEMO_PASSWORD=isolated-password\n', encoding='utf-8')
            env = {key: value for key, value in os.environ.items()
                   if not key.startswith(('DEMO_', 'DB_', 'PYTHON'))}
            env.update(PYTHONPATH=directory + os.pathsep + str(Path.cwd()),
                       DJANGO_SETTINGS_MODULE='TestCreator.settings',
                       DB_BACKEND='mysql', DB_HOST='must-not-connect.invalid', DB_PORT='3306',
                       DB_NAME='unused', DB_USER='unused', DB_PASSWORD='unused')
            code = (
                'import django; django.setup(); '
                'from unittest.mock import patch; '
                'from django.core.management import call_command; '
                "patcher=patch('accounts.management.commands.initialize_runtime.call_command'); "
                'dispatch=patcher.start(); call_command("initialize_runtime"); '
                'print([call.args[0] for call in dispatch.call_args_list])'
            )
            for mode, expected in ((None, "['ensure_demo_user', 'seed_demo']"),
                                   ('false', "['ensure_superuser']")):
                if mode is not None:
                    env['DEMO_MODE'] = mode
                result = subprocess.run([sys.executable, '-c', code], cwd=root, env=env,
                                        capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr.decode())
                self.assertEqual(result.stdout.decode().strip(), expected)

    def test_files_persist_and_new_instance_restores_initial_state(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            Path(root, 'file_demo.py').write_text(
                'from TestCreator.production import *\n'
                'DATABASES["default"]["NAME"] = os.environ["TEST_DEMO_DB"]\n', encoding='utf-8')
            env = os.environ | {'PYTHONPATH': directory + os.pathsep + str(Path.cwd()),
                'DJANGO_SETTINGS_MODULE': 'file_demo', 'DEMO_MODE': 'TRUE',
                'DEMO_PASSWORD': 'isolated-demo-password', 'DEMO_USERNAME': 'demo',
                'OPENAI_API_KEY': 'test-only', 'DB_BACKEND': 'invalid',
                'DB_HOST': 'must-not-connect.invalid', 'DB_SSL_CA': '/missing.pem'}

            def run(*args):
                result = subprocess.run([sys.executable, 'manage.py', *args], env=env,
                                        capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr.decode())

            def initialize():
                for args in [('migrate', '--noinput'), ('initialize_runtime',)]:
                    run(*args)

            env['TEST_DEMO_DB'] = str(root / 'first.sqlite3')
            initialize()
            run('shell', '-c',
                "from vocab.models import Word; from accounts.models import AdminUser; "
                "from ocr.models import APICostLog; from django.contrib.sessions.models import Session; "
                "from django.utils import timezone; w=Word.objects.first(); w.term='changed'; w.save(); "
                "Word.objects.exclude(pk=w.pk).first().delete(); "
                "APICostLog.objects.create(user=AdminUser.objects.get(username='demo'), "
                "estimated_cost=0.01,request_id='isolated'); "
                "Session.objects.create(session_key='isolated',session_data='',expire_date=timezone.now())")
            initialize()
            run('shell', '-c',
                "from vocab.models import Word; from ocr.models import APICostLog; "
                "from django.contrib.sessions.models import Session; "
                "assert Word.objects.count()==69; assert Word.objects.first().term=='changed'; "
                "assert APICostLog.objects.count()==1; assert Session.objects.count()==1")
            env['TEST_DEMO_DB'] = str(root / 'second.sqlite3')
            initialize()
            run('shell', '-c',
                "from vocab.models import Word; from ocr.models import APICostLog; "
                "from django.contrib.sessions.models import Session; "
                "assert Word.objects.count()==70; assert Word.objects.first().term=='apple'; "
                "assert APICostLog.objects.count()==0; assert Session.objects.count()==0")
            env['TEST_DEMO_DB'] = str(root / 'first.sqlite3')
            run('shell', '-c', "from vocab.models import Word; assert Word.objects.count()==69")
            env['TEST_DEMO_DB'] = str(root / 'missing-directory' / 'unwritable.sqlite3')
            result = subprocess.run([sys.executable, 'manage.py', 'migrate', '--noinput'],
                                    env=env, capture_output=True, timeout=30)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('unable to open database file', result.stderr.decode())
