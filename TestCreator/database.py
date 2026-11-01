"""Explicit database configuration shared by development and production."""

from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def database_config(environ, *, collectstatic=False):
    backend = environ.get("DB_BACKEND", "")
    engines = {"mysql": "django.db.backends.mysql", "tidb": "django_tidb"}
    if backend and backend not in engines:
        raise ImproperlyConfigured("DB_BACKEND must be mysql or tidb.")
    # Static collection needs no DB; this backend cannot connect or create one.
    if collectstatic:
        return {"ENGINE": "django.db.backends.dummy"}
    required = ["DB_BACKEND", "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    if backend == "tidb":
        required.append("DB_SSL_CA")
    missing = [key for key in required if not environ.get(key)]
    if missing:
        raise ImproperlyConfigured("Missing database settings: " + ", ".join(missing))
    port = environ["DB_PORT"]
    if not port.isascii() or not port.isdecimal() or not 1 <= int(port) <= 65535:
        raise ImproperlyConfigured("DB_PORT must be an integer between 1 and 65535.")
    options = {
        "charset": "utf8mb4",
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        "ssl_mode": "DISABLED",
    }
    ca = environ.get("DB_SSL_CA")
    if ca:
        if not Path(ca).is_file():
            raise ImproperlyConfigured("DB_SSL_CA must point to an existing CA certificate file.")
        options["ssl"] = {"ca": ca}
        options["ssl_mode"] = "VERIFY_IDENTITY"
    return {
        "ENGINE": engines[backend], "HOST": environ["DB_HOST"], "PORT": port,
        "NAME": environ["DB_NAME"], "USER": environ["DB_USER"],
        # Credentials are opaque: preserve whitespace and never print values.
        "PASSWORD": environ["DB_PASSWORD"], "OPTIONS": options,
    }
