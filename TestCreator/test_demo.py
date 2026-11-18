"""明示的なデモ設定、管理画面の遮断、限定した案内の検証。"""
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import io
import json
import pypdf
from accounts.models import AdminUser
from wordbank.models import WordList
from vocab.models import Word
from ocr.models import APICostLog


class DemoSafetyTests(TestCase):
    def test_final_database_settings_are_checked_before_commands(self):
        for engine in ("django.db.backends.mysql", "django_tidb", "django.db.backends.dummy"):
            with self.subTest(engine=engine), patch.object(settings, 'DATABASES', {"default": {"ENGINE": engine}}):
                with self.assertRaises(ImproperlyConfigured):
                    apps.get_app_config("home").ready()

    @override_settings(DEMO_PASSWORD="")
    def test_password_is_required_when_enabled(self):
        with self.assertRaises(ImproperlyConfigured):
            apps.get_app_config("home").ready()

    @override_settings(DEMO_MODE=False, DEMO_PASSWORD='')
    def test_normal_database_settings_do_not_require_demo_credentials(self):
        for engine in ('django.db.backends.mysql', 'django_tidb'):
            with patch.object(settings, 'DATABASES', {'default': {'ENGINE': engine}}):
                apps.get_app_config('home').ready()

    def test_secondary_database_cannot_bypass_demo_safety(self):
        databases = {'default': {'ENGINE': 'django.db.backends.sqlite3'},
                     'secondary': {'ENGINE': 'django.db.backends.mysql'}}
        with patch.object(settings, 'DATABASES', databases), self.assertRaises(ImproperlyConfigured):
            apps.get_app_config('home').ready()

    def test_admin_is_denied_for_every_method_and_session(self):
        users = [None, AdminUser.objects.create_user("shared", "password"),
                 AdminUser.objects.create_user("staff", "password", is_staff=True),
                 AdminUser.objects.create_superuser("root", "password")]
        for user in users:
            client = Client(enforce_csrf_checks=True)
            if user:
                client.force_login(user)
            csrf_token = 'a' * 32
            client.cookies[settings.CSRF_COOKIE_NAME] = csrf_token
            for path in ("/admin", "/admin/", "/admin/login/", "/admin/accounts/adminuser/",
                         "/admin/accounts/adminuser/1/change/", "/admin/accounts/adminuser/1/delete/",
                         "/admin/password_change/"):
                for method in ("get", "post", "head", "options", "put", "patch", "delete"):
                    with self.subTest(user=user, path=path, method=method):
                        response = getattr(client, method)(path, HTTP_X_CSRFTOKEN=csrf_token)
                        self.assertEqual(response.status_code, 403)
                        if method != 'head':
                            self.assertContains(response, 'デモ環境では管理画面を利用できません。', status_code=403)

    def test_credentials_are_limited_to_home_and_login(self):
        for debug in (True, False):
            with override_settings(DEBUG=debug, SECRET_KEY="private-secret-marker", API_KEY="private-api-marker"):
                for path in ("/", "/accounts/login/"):
                    response = self.client.get(path)
                    self.assertContains(response, settings.DEMO_PASSWORD)
                    self.assertContains(response, "デモ環境")
                    self.assertContains(response, "個人情報")
                    self.assertNotContains(response, "private-secret-marker")
                    self.assertNotContains(response, "private-api-marker")
                response = self.client.get("/quiz/configure/")
                self.assertContains(response, "デモ環境")
                self.assertNotContains(response, settings.DEMO_PASSWORD)

    @override_settings(DEMO_MODE=False)
    def test_normal_mode_keeps_admin_and_hides_demo_information(self):
        self.assertEqual(self.client.get("/admin/").status_code, 302)
        normal = AdminUser.objects.create_user('normal', 'password')
        self.client.force_login(normal)
        self.assertEqual(self.client.get('/admin/').status_code, 302)
        root = AdminUser.objects.create_superuser('normal-root', 'password')
        self.client.force_login(root)
        self.assertEqual(self.client.get('/admin/').status_code, 200)
        for debug in (True, False):
            with override_settings(DEBUG=debug):
                for path in ("/", "/accounts/login/", "/quiz/configure/"):
                    response = self.client.get(path)
                    self.assertNotContains(response, "デモ環境")
                    self.assertNotContains(response, settings.DEMO_PASSWORD)


class DemoWorkflowTests(TestCase):
    def test_existing_workflow_with_real_login_csrf_ocr_and_pdf(self):
        user = AdminUser.objects.create_user(settings.DEMO_USERNAME, settings.DEMO_PASSWORD)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.get('/').status_code, 200)
        self.assertEqual(client.get(reverse('accounts:login')).status_code, 200)
        before = client.cookies['csrftoken'].value
        self.assertEqual(client.post(reverse('accounts:login'), {
            'username': settings.DEMO_USERNAME, 'password': settings.DEMO_PASSWORD,
            'csrfmiddlewaretoken': before,
        }).status_code, 302)
        self.assertNotEqual(before, client.cookies['csrftoken'].value)

        def post(name, data, *, encoded=False):
            options = {'HTTP_X_CSRFTOKEN': client.cookies['csrftoken'].value}
            if encoded:
                options['content_type'] = 'application/json'
                data = json.dumps(data)
            return client.post(reverse(name), data, **options)

        response = post('wordbank:create', {'name': 'デモ検証用単語帳'})
        self.assertEqual(response.status_code, 201)
        wordlist_id = response.json()['id']
        self.assertEqual(WordList.objects.get(pk=wordlist_id).created_by, user)
        self.assertIn({'id': wordlist_id, 'name': 'デモ検証用単語帳'},
                      client.get(reverse('wordbank:all_wordlist')).json()['wordlists'])
        for name in ('vocab:reference', 'vocab:editor', 'quiz:configure'):
            self.assertContains(client.get(reverse(name)), 'デモ環境')
        self.assertContains(client.get(reverse('ocr:interface'), {'wordlist': wordlist_id}), 'デモ環境')
        response = post('vocab:register', {'wordlist': wordlist_id, 'number': 1,
                                         'term': 'apple', 'meaning': 'りんご'})
        self.assertEqual(response.status_code, 201)
        word_id = response.json()['id']
        self.assertEqual(Word.objects.get(pk=word_id).latest_edited_by, user)
        previous_editor = AdminUser.objects.create_user('previous-editor', 'password')
        Word.objects.filter(pk=word_id).update(latest_edited_by=previous_editor)
        self.assertEqual(post('vocab:update', {'id': word_id, 'number': 1, 'term': 'Apple',
                                             'meaning': '林檎'}, encoded=True).status_code, 200)
        updated_word = Word.objects.get(pk=word_id)
        self.assertEqual(updated_word.latest_edited_by, user)
        self.assertEqual((updated_word.number, updated_word.term, updated_word.meaning), (1, 'Apple', '林檎'))
        self.assertEqual(post('wordbank:read', {'id': wordlist_id}, encoded=True).json()['words'][0]['meaning'], '林檎')
        # 外部API応答だけを置換し、抽出・費用計算・フォーム・保存は実処理を通す。
        completion = SimpleNamespace(id='test-request', model='gpt-4o-mini',
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=50),
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"book":{"number":2,"meaning":"本"}}'))])
        with override_settings(API_KEY='test-only-api-key'), patch('openai.resources.chat.completions.Completions.create', return_value=completion):
            response = post('ocr:ocr', {'files': SimpleUploadedFile('sample.jpg', b'test-image', content_type='image/jpeg')})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(APICostLog.objects.get(request_id='test-request').user, user)
        self.assertGreater(APICostLog.objects.get().estimated_cost, 0)
        # 費用のUI戻り値の既存不整合は#33で扱う。
        extracted = response.json()['words'][0]
        registered = post('vocab:register', extracted | {'wordlist': wordlist_id})
        self.assertEqual(registered.status_code, 201)
        self.assertEqual(Word.objects.get(pk=registered.json()['id']).latest_edited_by, user)
        configure = {'wordlistId': wordlist_id, 'ranges': [{'start': 1, 'end': 2}],
                     'numQuestion': 2, 'sequence': 'sequence', 'format': 'qfr-tm'}
        self.assertEqual(post('quiz:preview', configure, encoded=True).status_code, 200)
        preview = client.get(reverse('quiz:preview'))
        self.assertContains(preview, '林檎')
        self.assertNotContains(preview, 'デモ環境')
        with TemporaryDirectory() as directory, override_settings(OUTPUT_PDF_DIR=directory):
            response = post('quiz:create', configure, encoded=True)
            self.assertEqual(response.status_code, 200)
            pdf = pypdf.PdfReader(io.BytesIO(b''.join(response.streaming_content)))
            self.assertGreaterEqual(len(pdf.pages), 2)
            text = ''.join(page.extract_text() for page in pdf.pages)
            self.assertIn('林檎', text)
            self.assertNotIn('デモ環境', text)
        self.assertEqual(post('vocab:delete', {'ids': [word_id]}, encoded=True).status_code, 200)
        self.assertFalse(Word.objects.filter(pk=word_id).exists())
        self.assertEqual(post('wordbank:delete', {'id': wordlist_id}, encoded=True).status_code, 200)
        self.assertFalse(WordList.objects.filter(pk=wordlist_id).exists())
