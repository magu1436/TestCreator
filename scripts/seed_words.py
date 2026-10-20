#!/usr/bin/env python
"""英単語50語のテスト用単語帳を作成する。

実行例（マイグレーション実行済みの開発環境）:
    python scripts/seed_words.py --username admin

既存ユーザーを作成者に指定する。同じユーザー・単語帳名で再実行しても
登録済みの単語番号は追加・上書きしない。
"""

import argparse
import os
from pathlib import Path
import sys


WORDS = [
    ("apple", "りんご"),
    ("book", "本"),
    ("cat", "猫"),
    ("dog", "犬"),
    ("water", "水"),
    ("food", "食べ物"),
    ("house", "家"),
    ("school", "学校"),
    ("friend", "友達"),
    ("family", "家族"),
    ("time", "時間"),
    ("day", "日"),
    ("night", "夜"),
    ("morning", "朝"),
    ("work", "働く"),
    ("study", "勉強する"),
    ("read", "読む"),
    ("write", "書く"),
    ("speak", "話す"),
    ("listen", "聞く"),
    ("walk", "歩く"),
    ("run", "走る"),
    ("eat", "食べる"),
    ("drink", "飲む"),
    ("sleep", "眠る"),
    ("think", "考える"),
    ("know", "知っている"),
    ("learn", "学ぶ"),
    ("make", "作る"),
    ("use", "使う"),
    ("open", "開ける"),
    ("close", "閉める"),
    ("start", "始める"),
    ("finish", "終える"),
    ("help", "助ける"),
    ("buy", "買う"),
    ("give", "与える"),
    ("take", "取る"),
    ("come", "来る"),
    ("go", "行く"),
    ("good", "良い"),
    ("bad", "悪い"),
    ("big", "大きい"),
    ("small", "小さい"),
    ("new", "新しい"),
    ("old", "古い"),
    ("happy", "幸せな"),
    ("beautiful", "美しい"),
    ("easy", "簡単な"),
    ("important", "重要な"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True, help="作成者にする既存ユーザー名")
    parser.add_argument("--name", default="テスト用英単語50", help="単語帳名（30文字以内）")
    args = parser.parse_args()
    if not args.name.strip() or len(args.name) > 30:
        parser.error("単語帳名は1〜30文字で指定してください。")

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TestCreator.settings")
    import django

    django.setup()

    from django.contrib.auth import get_user_model
    from django.db import transaction
    from vocab.models import Word
    from wordbank.models import WordList

    user = get_user_model().objects.filter(username=args.username).first()
    if user is None:
        parser.error(f"ユーザー {args.username!r} が存在しません。既存ユーザーを指定してください。")

    with transaction.atomic():
        wordlist, _ = WordList.objects.get_or_create(name=args.name, created_by=user)
        created_count = 0
        for number, (term, meaning) in enumerate(WORDS, start=1):
            _, created = Word.objects.get_or_create(
                wordlist=wordlist,
                number=number,
                defaults={"term": term, "meaning": meaning, "latest_edited_by": user},
            )
            created_count += int(created)

    print(f"単語帳: {wordlist.name} (ID: {wordlist.pk})")
    print(f"番号1〜50: {created_count}語追加、{len(WORDS) - created_count}語登録済み")


if __name__ == "__main__":
    main()
