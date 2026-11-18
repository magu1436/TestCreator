from django.test import TestCase
from django.urls import reverse

from accounts.models import AdminUser
from wordbank.models import WordList


class ReferenceCsrfCookieTests(TestCase):
    """単語帳参照画面がCSRF Cookieを発行することの回帰テスト。"""

    def setUp(self):
        self.user = AdminUser.objects.create_user("tester", password="pass-1234")
        self.wordlist = WordList.objects.create(name="テスト単語帳", created_by=self.user)
        self.url = reverse("vocab:reference")

    def assert_csrf_cookie(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)
        self.assertTrue(response.cookies["csrftoken"].value)

    def test_anonymous_first_visit_sets_csrf_cookie(self):
        self.assert_csrf_cookie(self.client.get(self.url))

    def test_logged_in_visit_sets_csrf_cookie(self):
        self.client.force_login(self.user)
        self.assert_csrf_cookie(self.client.get(self.url))
