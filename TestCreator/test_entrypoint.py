"""Exercise the production shell entrypoint without starting a DB or web server."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless


@skipUnless(shutil.which("sh"), "Requires a POSIX shell")
class EntrypointTests(TestCase):
    def run_entrypoint(self, fail_at="", port=None):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / "calls"
            for command in ("python", "gunicorn"):
                stub = root / command
                stub.write_text(
                    f"#!{sys.executable}\n"
                    "import os, sys\n"
                    "from pathlib import Path\n"
                    "call = Path(sys.argv[0]).name + ' ' + ' '.join(sys.argv[1:])\n"
                    "with open(os.environ['CALL_LOG'], 'a') as log: log.write(call + '\\n')\n"
                    "sys.exit(7 if os.environ.get('FAIL_AT') in sys.argv[1:] else 0)\n",
                    encoding="utf-8",
                )
                stub.chmod(0o755)
            env = dict(os.environ, PATH=f"{root}:{os.environ.get('PATH', '')}",
                       CALL_LOG=str(log), FAIL_AT=fail_at)
            env.pop("PORT", None)
            if port is not None:
                env["PORT"] = port
            result = subprocess.run(
                ["sh", str(Path(__file__).resolve().parent.parent / "entrypoint.sh")],
                env=env, capture_output=True,
            )
            calls = log.read_text().splitlines()
        return result, calls

    def test_startup_order_and_port(self):
        for port, expected in ((None, "8080"), ("18080", "18080")):
            result, calls = self.run_entrypoint(port=port)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(calls, [
                "python manage.py migrate --noinput",
                "python manage.py ensure_superuser",
                "gunicorn TestCreator.wsgi:application "
                f"--bind 0.0.0.0:{expected} --workers 2 --threads 4 --timeout 120",
            ])

    def test_failed_initialization_prevents_server_start(self):
        for command, expected_count in (("migrate", 1), ("ensure_superuser", 2)):
            result, calls = self.run_entrypoint(fail_at=command)
            self.assertEqual(result.returncode, 7)
            self.assertEqual(len(calls), expected_count)
            self.assertFalse(any(call.startswith("gunicorn") for call in calls))
