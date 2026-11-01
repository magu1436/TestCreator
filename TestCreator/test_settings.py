"""Check real settings imports in isolated processes without a database or API calls."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase


class EnvironmentSettingsTests(TestCase):
    def import_settings(self, module, variables, assertion, dotenv=""):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "TestCreator"
            package.mkdir()
            (package / "__init__.py").touch()
            for name in ("settings.py", "production.py", "database.py"):
                shutil.copyfile(Path(__file__).with_name(name), package / name)
            (root / ".env").write_text(dotenv, encoding="utf-8")
            env = {key: value for key, value in os.environ.items()
                   if key not in {"API_KEY", "OPENAI_API_KEY", "OUTPUT_PDF_DIR", "ALLOWED_HOSTS",
                                  "CSRF_TRUSTED_ORIGINS", "DJANGO_SECRET_KEY", "DJANGO_DEBUG"}
                   and not key.startswith(("DB_", "PYTHON"))}
            env.update(variables)
            code = (f"import sys; sys.path.insert(0, {str(root)!r}); "
                    "sys.argv=['manage.py', 'collectstatic']; "
                    f"import {module} as settings; " + assertion)
            # A different cwd proves .env is loaded relative to the project root.
            result = subprocess.run([sys.executable, "-c", code], cwd=package,
                                    env=env, capture_output=True)
        self.assertEqual(result.returncode, 0, "Settings import assertion failed")
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.stderr, b"")

    def test_ocr_key_precedence_in_development_and_production(self):
        cases = [({}, ""), ({"API_KEY": "legacy-test-value"}, "legacy-test-value"),
                 ({"OPENAI_API_KEY": "preferred-test-value"}, "preferred-test-value"),
                 ({"OPENAI_API_KEY": "preferred-test-value", "API_KEY": "legacy-test-value"},
                  "preferred-test-value"),
                 ({"OPENAI_API_KEY": "", "API_KEY": "legacy-test-value"}, "")]
        for module in ("TestCreator.settings", "TestCreator.production"):
            for variables, expected in cases:
                with self.subTest(module=module, keys=sorted(variables)):
                    self.import_settings(module, variables,
                                         f"assert settings.API_KEY == {expected!r}")

    def test_project_dotenv_is_loaded_without_overriding_process_environment(self):
        for module in ("TestCreator.settings", "TestCreator.production"):
            self.import_settings(module, {"OPENAI_API_KEY": "process-test-value"},
                                 "assert settings.API_KEY == 'process-test-value'",
                                 "OPENAI_API_KEY=file-test-value\n")
            self.import_settings(module, {}, "assert settings.API_KEY == 'file-test-value'",
                                 "OPENAI_API_KEY=file-test-value\n")

    def test_production_security_and_static_configuration(self):
        self.import_settings("TestCreator.production", {
            "DJANGO_SECRET_KEY": "test-only-secret", "DJANGO_DEBUG": "false",
            "ALLOWED_HOSTS": "one.example,two.example",
            "CSRF_TRUSTED_ORIGINS": "https://one.example,https://two.example",
        }, "assert settings.SECRET_KEY == 'test-only-secret'; "
           "assert settings.DEBUG is False; "
           "assert settings.ALLOWED_HOSTS == ['one.example', 'two.example']; "
           "assert settings.CSRF_TRUSTED_ORIGINS == ['https://one.example', 'https://two.example']; "
           "assert settings.MIDDLEWARE[1] == 'whitenoise.middleware.WhiteNoiseMiddleware'; "
           "assert settings.STATIC_URL == '/static/'; "
           "assert settings.STORAGES['staticfiles']['BACKEND'] == "
           "'whitenoise.storage.CompressedStaticFilesStorage'")

    def test_production_debug_defaults_to_false_and_csrf_to_empty(self):
        self.import_settings("TestCreator.production", {},
                             "assert settings.DEBUG is False; "
                             "assert settings.CSRF_TRUSTED_ORIGINS == []")
