from django.db import models
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin

class AdminUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, password=None, **extra_fields):
        """
        通常ユーザー作成.  
        username と password は必須.
        """
        if not username:
            raise ValueError("username を必ず指定してください")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, password=None, **extra_fields):
        """
        管理者ユーザー作成.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("superuser は is_staff=True にしてください.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("superuser は is_superuser=True にしてください.")
        
        return self.create_user(username, password, **extra_fields)


class AdminUser(AbstractBaseUser, PermissionsMixin):
    """
    カスタムユーザー.
    """

    username = models.CharField("ユーザー名", max_length=150, unique=True)
    is_staff = models.BooleanField("管理サイト権限", default=False)
    is_active = models.BooleanField("アクティブ", default=True)
    date_joined = models.DateTimeField("登録日時", auto_now_add=True)

    # ユーザー作成に用いるマネージャー
    objects = AdminUserManager()

    # 認証に用いるフィールド
    USERNAME_FIELD = "username"

    # createsuperuser 時に求める追加フィールド. 今回は空.
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "管理ユーザー"
        verbose_name_plural = "管理ユーザー一覧"
    
    def __str__(self):
        return self.username