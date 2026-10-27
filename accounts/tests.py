import os
from io import StringIO
from typing import cast
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from accounts.models import AdminUser, AdminUserManager


users = cast(AdminUserManager, AdminUser.objects)


class EnsureSuperuserTests(TestCase):
    def run_command(self, username="", password=""):
        output = StringIO()
        with patch.dict(os.environ, {
            "DJANGO_SUPERUSER_USERNAME": username,
            "DJANGO_SUPERUSER_PASSWORD": password,
        }):
            call_command("ensure_superuser", stdout=output)
        return output.getvalue()

    def test_unconfigured_skips_creation(self):
        self.assertIn("skipped", self.run_command())
        self.assertFalse(users.exists())

    def test_partial_configuration_fails_without_exposing_password(self):
        for username, password in [("admin", ""), ("", "private-value")]:
            with self.subTest(username=username):
                with self.assertRaises(CommandError) as error:
                    self.run_command(username, password)
                self.assertNotIn("private-value", str(error.exception))
        self.assertFalse(users.exists())

    def test_creates_active_superuser_with_hashed_password(self):
        password = "  private-value  "
        output = self.run_command("admin", password)
        user = users.get(username="admin")
        self.assertTrue(user.is_active and user.is_staff and user.is_superuser)
        self.assertTrue(user.check_password(password))
        self.assertNotEqual(user.password, password)
        self.assertNotIn(password, output)

    def test_existing_superuser_and_password_are_unchanged_on_repeated_runs(self):
        self.run_command("admin", "original-password")
        self.assertIn("unchanged", self.run_command("admin", "replacement-password"))
        user = users.get(username="admin")
        self.assertTrue(user.check_password("original-password"))
        self.assertEqual(users.count(), 1)

    def test_existing_regular_user_is_not_promoted(self):
        user = users.create_user("admin", "original-password")
        with self.assertRaises(CommandError):
            self.run_command("admin", "replacement-password")
        user.refresh_from_db(from_queryset=None)
        self.assertFalse(user.is_staff or user.is_superuser)
        self.assertTrue(user.check_password("original-password"))

    def test_inactive_superuser_is_not_reactivated(self):
        user = users.create_superuser(
            "admin", "original-password", is_active=False
        )
        with self.assertRaises(CommandError):
            self.run_command("admin", "replacement-password")
        user.refresh_from_db(from_queryset=None)
        self.assertFalse(user.is_active)
