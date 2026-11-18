from django.test import TestCase
from django.urls import reverse

from accounts.models import AdminUser
from wordbank.models import WordList


class InterfaceCsrfCookieTests(TestCase):
    """OCR画面がCSRF Cookieを発行することの回帰テスト。"""

    def setUp(self):
        user = AdminUser.objects.create_user("tester", password="pass-1234")
        self.wordlist = WordList.objects.create(name="テスト単語帳", created_by=user)

    def test_anonymous_first_visit_sets_csrf_cookie(self):
        response = self.client.get(reverse("ocr:interface"), {"wordlist": self.wordlist.pk})
        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)
        self.assertTrue(response.cookies["csrftoken"].value)
