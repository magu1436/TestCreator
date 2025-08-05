from django.db import models
from django.conf import settings


class WordList(models.Model):
    """単語帳のモデル
    
    Fields:
        name(CharField): 単語帳名
        created_by(ForeignKey): 作成者（ユーザー）
        created_at(DateTimeField): 作成日時
    """
    name = models.CharField("単語名", max_length=30)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="作成者",
        on_delete=models.PROTECT,
        related_name="created_wordlists",   # userにcreated_wordlistsというメソッドを追加して、user側から一覧を取得できるようにする
    )
    created_at = models.DateTimeField("作成日時", auto_now_add=True)

    def __str__(self):
        return self.name