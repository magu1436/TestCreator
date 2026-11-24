"""環境ファイルと派生設定を反映した起動時初期化を選択する。"""
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '有効なDjango設定に従って通常環境またはデモ環境を初期化します。'

    def handle(self, *args, **options):
        if settings.DEMO_MODE:
            call_command('ensure_demo_user')
            call_command('seed_demo')
        else:
            call_command('ensure_superuser')
