"""公開デモ専用のサンプルを初回だけ投入する。"""
import json
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.management.commands.ensure_demo_user import require_demo
from vocab.models import Word
from wordbank.models import WordList


class Command(BaseCommand):
    help = 'デモDBの初回だけ公開用サンプルを投入します。'

    def handle(self, *args, **options):
        require_demo()
        DemoInitialization = apps.get_model('demo', 'DemoInitialization')
        with transaction.atomic():
            _, created = DemoInitialization.objects.get_or_create(key='initial-samples')
            if not created:
                self.stdout.write('サンプルは投入済みです。現在のデータを維持します。')
                return
            user = get_user_model().objects.get(username=settings.DEMO_USERNAME)
            source = Path(settings.BASE_DIR) / 'demo' / 'data' / 'samples.json'
            samples = json.loads(source.read_text(encoding='utf-8-sig'))
            for sample in samples['wordlists']:
                wordlist = WordList.objects.create(name=sample['name'], created_by=user)
                Word.objects.bulk_create([
                    Word(wordlist=wordlist, number=word['number'], term=word['term'],
                         meaning=word['meaning'], latest_edited_by=user)
                    for word in sample['words']
                ])
        self.stdout.write('公開用サンプルを投入しました。')
