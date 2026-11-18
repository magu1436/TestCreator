"""デモ設定の安全確認と公開画面に必要な情報だけを提供する。"""
import sys

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseForbidden
from django.urls import reverse


def validate_demo_settings():
    """派生設定のDB選択が完了した後、DB操作より前に検証する。"""
    if not settings.DEMO_MODE or (len(sys.argv) > 1 and sys.argv[1] == 'collectstatic'):
        return
    if not settings.DEMO_PASSWORD or not settings.DEMO_USERNAME.strip():
        raise ImproperlyConfigured('DEMO_MODEにはDEMO_USERNAMEとDEMO_PASSWORDの設定が必要です。')
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
