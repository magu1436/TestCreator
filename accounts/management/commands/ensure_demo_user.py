"""デモ専用の共有ユーザーを安全な権限で準備する。"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from TestCreator.demo import validate_demo_settings


def require_demo():
    """通常環境ではDBへアクセスする前に拒否する。"""
    if not settings.DEMO_MODE:
        raise CommandError('デモ専用コマンドはDEMO_MODE=trueでのみ実行できます。')
    validate_demo_settings()


class Command(BaseCommand):
    help = 'active・非staff・非superuserのデモ共有ユーザーを準備します。'

    def handle(self, *args, **options):
        require_demo()
        with transaction.atomic():
            user, _ = get_user_model().objects.get_or_create(username=settings.DEMO_USERNAME)
            user.is_active = True
            user.is_staff = False
            user.is_superuser = False
            if not user.check_password(settings.DEMO_PASSWORD):
                user.set_password(settings.DEMO_PASSWORD)
            user.save()
            user.groups.clear()
            user.user_permissions.clear()
        self.stdout.write('デモ共有ユーザーを準備しました。')
