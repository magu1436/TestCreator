from django.db import models


class DemoInitialization(models.Model):
    """同じDBでサンプルの削除・編集を巻き戻さないための初回投入記録。"""

    key = models.CharField(max_length=50, primary_key=True)
    completed_at = models.DateTimeField(auto_now_add=True)
