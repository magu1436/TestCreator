"""既存の開発用データを初回だけ投入する暫定的な接続点。"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.management.commands.ensure_demo_user import require_demo
from home.models import DemoInitialization
from scripts.seed_words import WORDS
from vocab.models import Word
from wordbank.models import WordList


class Command(BaseCommand):
    help = 'デモDBの初回だけ暫定サンプルを投入します。公開用内容はIssue #30で整備します。'

    def handle(self, *args, **options):
        require_demo()
        with transaction.atomic():
            _, created = DemoInitialization.objects.get_or_create(key='initial-samples')
            if not created:
                self.stdout.write('サンプルは投入済みです。現在のデータを維持します。')
                return
            user = get_user_model().objects.get(username=settings.DEMO_USERNAME)
            wordlist = WordList.objects.create(name='テスト用英単語50', created_by=user)
            Word.objects.bulk_create([
                Word(wordlist=wordlist, number=number, term=term, meaning=meaning,
                     latest_edited_by=user)
                for number, (term, meaning) in enumerate(WORDS, start=1)
            ])
        self.stdout.write('暫定サンプルを投入しました。')
