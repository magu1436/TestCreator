from django.db import models
from wordbank.models import WordList
from django.conf import settings


class Word(models.Model):
    """単語のモデル"""
    number = models.PositiveIntegerField("単語番号")
    term = models.CharField(
        "単語",
        max_length=30
    )
    meaning = models.CharField(
        "意味",
        max_length=100,
    )
    wordlist = models.ForeignKey(
        WordList,
        on_delete=models.PROTECT,
        related_name="words",
        verbose_name="単語帳",
    )
    latest_edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="latest_edited_words",
        verbose_name="最終編集者",
    )
    latest_edited_at = models.DateTimeField(
        "最終更新日時",
        auto_now=True,
    )

    class Meta:
        ordering = ["wordlist", "number"]       # デフォルトの並び替えを定義
        verbose_name = "単語"                   # データベース編集時にここで指定した値が使われるらしい？
        verbose_name = "単語一覧"

    def __str__(self):
        return f"{self.wordlist} - {self.number}: {self.term}"