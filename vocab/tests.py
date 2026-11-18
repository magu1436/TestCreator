import json

from django.test import Client, TestCase
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

    def test_issued_cookie_passes_csrf_check_on_word_read(self):
        """発行したCookieで、画面表示時の単語読込POSTがCSRF検証を通る。"""
        client = Client(enforce_csrf_checks=True)
        token = client.get(self.url).cookies["csrftoken"].value
        response = client.post(
            reverse("wordbank:read"),
            json.dumps({"id": self.wordlist.pk}),
            content_type="application/json",
            headers={"X-CSRFToken": token},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])

    def test_unrelated_query_shows_default_wordlist(self):
        """wordlist 以外のクエリだけでも 500 にならず既定の単語帳を表示する。"""
        response = self.client.get(self.url, {"utm_source": "x"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["target_word_list"], self.wordlist)

    def test_non_numeric_wordlist_returns_404(self):
        self.assertEqual(self.client.get(self.url, {"wordlist": "abc"}).status_code, 404)
