"""実際の標準出力ハンドラと非DEBUG時の応答を、DB不要の別プロセスで確認する。"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from textwrap import dedent
from unittest import TestCase


class SecurityLoggingTests(TestCase):
    def run_logging(self, code):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'TestCreator'
            package.mkdir()
            (package / '__init__.py').touch()
            for name in ('settings.py', 'production.py', 'database.py', 'demo.py'):
                shutil.copyfile(Path(__file__).with_name(name), package / name)
            (root / 'urls.py').write_text('urlpatterns = []\n', encoding='utf-8')
            # リポジトリの.envや実行環境の認証情報を子プロセスへ持ち込まない。
            env = {key: value for key, value in os.environ.items()
                   if key in {'PATH', 'SystemRoot', 'SYSTEMROOT', 'TEMP', 'TMP', 'HOME', 'LANG'}}
            env.update(DJANGO_SETTINGS_MODULE='TestCreator.production', DJANGO_DEBUG='false',
                       DJANGO_SECRET_KEY='logging-test-only-secret', ALLOWED_HOSTS='allowed.example',
                       OUTPUT_PDF_DIR=str(root / 'exports'))
            setup = """
                import sys
                sys.argv = ['manage.py', 'collectstatic']
                from django.conf import settings
                settings.INSTALLED_APPS = []
                settings.MIDDLEWARE = ['django.middleware.common.CommonMiddleware']
                settings.ROOT_URLCONF = 'urls'
                import django
                django.setup()
                assert settings.DEBUG is False
            """
            result = subprocess.run([sys.executable, '-c', dedent(setup) + dedent(code)],
                                    cwd=root, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        return result.stdout

    def test_security_warning_and_error_use_stdout_once_without_info(self):
        output = self.run_logging("""
            import logging
            logging.getLogger('django.security').warning('security-warning-marker')
            logging.getLogger('django.security').error('security-error-marker')
            logging.getLogger('django.security').info('security-info-marker')
            logging.getLogger('django.security.DisallowedHost').warning('host-child-marker')
            logging.getLogger('django.security.csrf').warning('csrf-child-marker')
            logging.getLogger('ocr').info('ocr-info-marker')
        """)
        self.assertEqual(output.splitlines(), [
            'WARNING django.security: security-warning-marker',
            'ERROR django.security: security-error-marker',
            'WARNING django.security.DisallowedHost: host-child-marker',
            'WARNING django.security.csrf: csrf-child-marker',
            'INFO ocr: ocr-info-marker',
        ])

    def test_invalid_host_logs_reason_once_but_returns_generic_400(self):
        output = self.run_logging("""
            from django.test import Client
            response = Client().get('/', HTTP_HOST='invalid.example')
            assert response.status_code == 400
            body = response.content.decode()
            assert 'Bad Request' in body
            assert 'Invalid HTTP_HOST' not in body
            assert 'invalid.example' not in body
            assert 'Traceback' not in body
            assert 'DisallowedHost' not in body
        """)
        self.assertEqual(output.count('ERROR django.security.DisallowedHost:'), 1)
        self.assertIn("Invalid HTTP_HOST header: 'invalid.example'", output)
