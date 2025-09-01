from django.db import models
from django.conf import settings


class APICostLog(models.Model):
    """ChatGPTの使用履歴用のデータ"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="利用者",
        on_delete=models.PROTECT,
    )
    estimated_cost = models.FloatField(
        verbose_name="推定費用",
    )
    request_id = models.CharField(
        max_length=64,
        verbose_name="リクエストID",
    )
    api_model = models.CharField(
        max_length=32,
        verbose_name="使用API名",
        default="openai",
    )
    created_at = models.DateTimeField(
        verbose_name="リクエスト日時",
        auto_now=True,
    )