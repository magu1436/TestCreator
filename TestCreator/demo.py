"""デモ設定の安全確認と公開画面に必要な情報だけを提供する。"""
import sys
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.http import HttpResponseForbidden
from django.urls import reverse

from .database import demo_database_path


def validate_demo_settings():
    """派生設定のDB選択が完了した後、DB操作より前に検証する。"""
    if bool(settings.DEMO_MODE) != apps.is_installed('demo'):
        raise ImproperlyConfigured('DEMO_MODEとdemoアプリの登録が一致しません。派生設定を確認してください。')
    if len(sys.argv) > 1 and sys.argv[1] == 'collectstatic':
        return
    if not settings.DEMO_MODE:
        for db in settings.DATABASES.values():
            if (db.get('ENGINE') == 'django.db.backends.sqlite3'
                    and Path(db.get('NAME', '')).resolve() == demo_database_path().resolve()):
                raise ImproperlyConfigured('通常モードではデモ専用DBを使用できません。派生設定でDBも選択し直してください。')
        return
    if not settings.DEMO_PASSWORD or not settings.DEMO_USERNAME.strip():
        raise ImproperlyConfigured('DEMO_MODEにはDEMO_USERNAMEとDEMO_PASSWORDの設定が必要です。')
    # 全モデルの登録後にフォームを読み、認証せず入力フィールドだけ検証する。
    from accounts.forms import LoginForm
    username_error = 'DEMO_USERNAMEは前後の空白がなく、NFKC正規化済みで、ログインフォームで有効な値を設定してください。'
    username_field = LoginForm().fields['username']
    try:
        username = username_field.clean(settings.DEMO_USERNAME)
    except ValidationError:
        raise ImproperlyConfigured(username_error) from None
    if (username != settings.DEMO_USERNAME
            or (username_field.max_length is not None and len(username) > username_field.max_length)):
        raise ImproperlyConfigured(username_error)
    if any(db.get('ENGINE') != 'django.db.backends.sqlite3' for db in settings.DATABASES.values()):
        raise ImproperlyConfigured('DEMO_MODEでは全DBにSQLiteが必要です。DBアクセスを拒否しました。')


class DemoAdminMiddleware:
    """CSRF・認証・URL補完より前に管理画面の全メソッドを拒否する。"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DEMO_MODE and (request.path_info == '/admin' or request.path_info.startswith('/admin/')):
            return HttpResponseForbidden('デモ環境では管理画面を利用できません。')
        return self.get_response(request)


def demo_context(request):
    """共有資格情報はホームと既存ログイン画面に限定する。"""
    context = {'demo_mode': settings.DEMO_MODE}
    if settings.DEMO_MODE and request.path_info in (reverse('home'), reverse('accounts:login')):
        context.update(demo_username=settings.DEMO_USERNAME, demo_password=settings.DEMO_PASSWORD)
    return context
