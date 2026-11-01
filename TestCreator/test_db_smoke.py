"""Runs on an isolated Django test database for either configured backend."""
import json

from django.test import TestCase
from django.urls import reverse

from accounts.models import AdminUser
from vocab.models import Word
from wordbank.models import WordList


class DatabaseWorkflowTests(TestCase):
    def test_login_and_wordlist_word_lifecycle(self):
        AdminUser.objects.create_user("db-smoke", "smoke-password")
        response = self.client.post(reverse("accounts:login"),
                                    {"username": "db-smoke", "password": "smoke-password"})
        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse("wordbank:create"), {"name": "日本語の単語帳"})
        self.assertEqual(response.status_code, 201)
        wordlist_id = response.json()["id"]
        response = self.client.post(reverse("vocab:register"), {
            "wordlist": wordlist_id, "number": 1, "term": "apple", "meaning": "りんご",
        })
        self.assertEqual(response.status_code, 201)
        word_id = response.json()["id"]
        response = self.client.post(reverse("vocab:update"), data=json.dumps({
            "id": word_id, "number": 2, "term": "Apple", "meaning": "林檎",
        }), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse("wordbank:read"),
                                    data=json.dumps({"id": wordlist_id}),
                                    content_type="application/json")
        self.assertEqual(response.json()["words"][0]["meaning"], "林檎")
        response = self.client.post(reverse("vocab:delete"),
                                    data=json.dumps({"ids": [word_id]}),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Word.objects.filter(pk=word_id).exists())
        response = self.client.post(reverse("wordbank:delete"),
                                    data=json.dumps({"id": wordlist_id}),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(WordList.objects.filter(pk=wordlist_id).exists())
