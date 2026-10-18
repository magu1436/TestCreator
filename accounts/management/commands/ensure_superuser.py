import os
from typing import cast

from django.core.management.base import BaseCommand, CommandError

from accounts.models import AdminUser, AdminUserManager


class Command(BaseCommand):
    help = "Create a superuser from environment variables if it does not exist."
    requires_migrations_checks = True

    def handle(self, *args, **options):
        # settings.py loads .env without overriding existing environment variables.
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        if not username and not password:
            self.stdout.write("Superuser environment variables are unset; skipped.")
            return
        if not username or not password:
            raise CommandError(
                "Set both DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD."
            )

        manager = cast(AdminUserManager, AdminUser.objects)
        user = manager.filter(username=username).first()
        if user is not None:
            if not (user.is_active and user.is_staff and user.is_superuser):
                raise CommandError(
                    "The configured username exists but is not an active superuser. "
                    "Review the existing account manually."
                )
            self.stdout.write("Superuser already exists; unchanged.")
            return

        manager.create_superuser(username=username, password=password)
        self.stdout.write(self.style.SUCCESS("Superuser created successfully."))
