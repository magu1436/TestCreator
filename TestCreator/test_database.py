import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from django.core.exceptions import ImproperlyConfigured

from .database import database_config


class DatabaseConfigurationTests(TestCase):
    def setUp(self):
        self.env = dict(DB_BACKEND="mysql", DB_HOST="db", DB_PORT="3306",
                        DB_NAME="testcreator", DB_USER="testcreator", DB_PASSWORD=" secret ")

    def test_mysql_and_password_preserved(self):
        config = database_config(self.env)
        self.assertEqual(config["ENGINE"], "django.db.backends.mysql")
        self.assertEqual(config["PASSWORD"], " secret ")
        self.assertNotIn("ssl", config["OPTIONS"])

    def test_debug_does_not_change_database(self):
        for value in ("true", "false"):
            self.assertEqual(database_config(dict(self.env, DJANGO_DEBUG=value)),
                             database_config(self.env))

    def test_missing_settings_fail_without_credentials_in_error(self):
        for key in self.env:
            env = dict(self.env)
            del env[key]
            with self.subTest(key=key), self.assertRaises(ImproperlyConfigured) as error:
                database_config(env)
            self.assertIn(key, str(error.exception))
            self.assertNotIn(" secret ", str(error.exception))

    def test_invalid_backend_and_port(self):
        for backend in ("sqlite", "unknown"):
            with self.assertRaises(ImproperlyConfigured):
                database_config(dict(self.env, DB_BACKEND=backend))
        for port in ("0", "65536", "abc", "３３０６"):
            with self.assertRaises(ImproperlyConfigured):
                database_config(dict(self.env, DB_PORT=port))

    def test_tidb_requires_existing_ca_and_enforces_tls(self):
        env = dict(self.env, DB_BACKEND="tidb")
        with self.assertRaises(ImproperlyConfigured):
            database_config(env)
        with self.assertRaises(ImproperlyConfigured):
            database_config(dict(env, DB_SSL_CA="/missing-ca.pem"))
        with TemporaryDirectory() as directory:
            ca = Path(directory) / "ca.pem"
            ca.touch()
            config = database_config(dict(env, DB_SSL_CA=str(ca)))
        self.assertEqual(config["ENGINE"], "django_tidb")
        self.assertEqual(config["OPTIONS"]["ssl_mode"], "VERIFY_IDENTITY")

    def test_static_collection_uses_nonconnecting_backend(self):
        self.assertEqual(database_config({}, collectstatic=True)["ENGINE"],
                         "django.db.backends.dummy")
        with self.assertRaises(ImproperlyConfigured):
            database_config({"DB_BACKEND": "sqlite"}, collectstatic=True)

    def test_old_environment_variables_are_not_accepted(self):
        with self.assertRaises(ImproperlyConfigured):
            database_config({"TIDB_HOST": "legacy", "MYSQL_DATABASE": "legacy"})

    def test_dotenv_does_not_override_process_environment(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env").write_text("DB_HOST=from-file\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-c", "import os; from dotenv import load_dotenv; "
                 "load_dotenv('.env'); assert os.environ['DB_HOST'] == 'from-process'"],
                cwd=root, env=dict(os.environ, DB_HOST="from-process"), capture_output=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr.decode())
