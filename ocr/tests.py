import datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import OperationalError, connection
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from TestCreator.settings import parse_ocr_daily_limit

from accounts.models import AdminUser

from .forms import APICostLogForm
from .models import APICostLog, OCRDailyUsage
from .quota import get_daily_limit, reserve_ocr_slot

LOCALDATE = "ocr.quota.timezone.localdate"


class DailyLimitResolutionTests(SimpleTestCase):
    """実効上限の解決(設定値とDEMO_MODEの組み合わせ)を確認する。"""

    @override_settings(OCR_DAILY_LIMIT=None, DEMO_MODE=True)
    def test_unset_in_demo_uses_default_10(self):
        self.assertEqual(get_daily_limit(), 10)

    @override_settings(OCR_DAILY_LIMIT=None, DEMO_MODE=False)
    def test_unset_in_normal_is_unlimited(self):
        self.assertIsNone(get_daily_limit())

    @override_settings(OCR_DAILY_LIMIT=-1, DEMO_MODE=True)
    def test_minus_one_is_unlimited_even_in_demo(self):
        self.assertIsNone(get_daily_limit())

    @override_settings(OCR_DAILY_LIMIT=0, DEMO_MODE=False)
    def test_zero_is_zero(self):
        self.assertEqual(get_daily_limit(), 0)

    @override_settings(OCR_DAILY_LIMIT=3, DEMO_MODE=False)
    def test_positive_is_used_as_is(self):
        self.assertEqual(get_daily_limit(), 3)


class ParseSettingTests(SimpleTestCase):
    """OCR_DAILY_LIMITの環境変数解釈を確認する。"""

    def test_unset_and_empty_are_none(self):
        for raw in (None, "", "  "):
            self.assertIsNone(parse_ocr_daily_limit(raw))

    def test_valid_values(self):
        self.assertEqual(parse_ocr_daily_limit("-1"), -1)
        self.assertEqual(parse_ocr_daily_limit("0"), 0)
        self.assertEqual(parse_ocr_daily_limit(" 25 "), 25)

    def test_invalid_values_raise(self):
        for raw in ("abc", "-2", "1.5"):
            with self.subTest(raw=raw):
                with self.assertRaisesMessage(ImproperlyConfigured, "OCR_DAILY_LIMIT"):
                    parse_ocr_daily_limit(raw)


class ReserveOcrSlotTests(TestCase):
    """予約の消費・拒否・日付切り替え・無制限時の挙動を確認する。"""

    day1 = datetime.date(2026, 1, 1)
    day2 = datetime.date(2026, 1, 2)

    @override_settings(OCR_DAILY_LIMIT=3)
    def test_allows_up_to_limit_then_refuses_without_incrementing(self):
        with patch(LOCALDATE, return_value=self.day1):
            results = [reserve_ocr_slot() for _ in range(5)]
        self.assertEqual([r.allowed for r in results], [True, True, True, False, False])
        self.assertEqual([r.used for r in results], [1, 2, 3, 3, 3])
        self.assertTrue(all(r.limit == 3 for r in results))
        self.assertEqual(OCRDailyUsage.objects.get(date=self.day1).count, 3)

    @override_settings(OCR_DAILY_LIMIT=1)
    def test_next_local_day_starts_fresh(self):
        with patch(LOCALDATE, return_value=self.day1):
            self.assertTrue(reserve_ocr_slot().allowed)
            self.assertFalse(reserve_ocr_slot().allowed)
        with patch(LOCALDATE, return_value=self.day2):
            self.assertTrue(reserve_ocr_slot().allowed)
        self.assertEqual(OCRDailyUsage.objects.get(date=self.day1).count, 1)
        self.assertEqual(OCRDailyUsage.objects.get(date=self.day2).count, 1)

    @override_settings(OCR_DAILY_LIMIT=-1)
    def test_unlimited_does_not_touch_db(self):
        with self.assertNumQueries(0):
            result = reserve_ocr_slot()
        self.assertTrue(result.allowed)
        self.assertIsNone(result.limit)
        self.assertEqual(OCRDailyUsage.objects.count(), 0)

    @override_settings(OCR_DAILY_LIMIT=0)
    def test_zero_refuses_without_db_access(self):
        with self.assertNumQueries(0):
            result = reserve_ocr_slot()
        self.assertFalse(result.allowed)
        self.assertEqual(result.limit, 0)

    @override_settings(OCR_DAILY_LIMIT=1)
    def test_logs_reservation_and_refusal(self):
        with patch(LOCALDATE, return_value=self.day1):
            with self.assertLogs("ocr.quota", level="INFO") as logs:
                reserve_ocr_slot()
                reserve_ocr_slot()
        self.assertEqual([r.levelname for r in logs.records], ["INFO", "WARNING"])
        self.assertIn("date=2026-01-01 used=1 limit=1", logs.output[0])
        self.assertIn("date=2026-01-01 used=1 limit=1", logs.output[1])


class ReserveOcrSlotConcurrencyTests(TransactionTestCase):
    """実DB上で複数スレッドが競合しても上限を超えないことを確認する。"""

    ATTEMPTS = 20
    LIMIT = 5

    @override_settings(OCR_DAILY_LIMIT=LIMIT)
    def test_concurrent_reservations_never_exceed_limit(self):
        barrier = Barrier(self.ATTEMPTS)

        def attempt():
            try:
                barrier.wait()
                return reserve_ocr_slot().allowed
            finally:
                connection.close()  # スレッドごとのDB接続を閉じる

        with ThreadPoolExecutor(max_workers=self.ATTEMPTS) as pool:
            allowed = list(pool.map(lambda _: attempt(), range(self.ATTEMPTS)))

        self.assertEqual(sum(allowed), self.LIMIT)
        usage = OCRDailyUsage.objects.get()
        self.assertEqual(usage.count, self.LIMIT)


CREATE = "openai.resources.chat.completions.Completions.create"


def _completion():
    """OpenAIの応答を模した最小のオブジェクト。"""
    return SimpleNamespace(
        id="test-request",
        model="gpt-4o-mini",
        usage=SimpleNamespace(prompt_tokens=100, completion_tokens=50),
        choices=[SimpleNamespace(message=SimpleNamespace(content='{"book":{"number":2,"meaning":"本"}}'))],
    )


@override_settings(API_KEY="test-only-api-key")
class OcrViewTests(TestCase):
    """OcrViewの利用枠・成功・失敗時の応答を、OpenAI呼び出しだけを置換して確認する。"""

    def setUp(self):
        self.user = AdminUser.objects.create_user("ocr-user", "password")
        self.client.force_login(self.user)

    def post(self, with_file=True):
        data = {"files": SimpleUploadedFile("sample.jpg", b"test-image", content_type="image/jpeg")} if with_file else {}
        return self.client.post(reverse("ocr:ocr"), data)

    @override_settings(OCR_DAILY_LIMIT=5, DEMO_MODE=True)
    def test_success_returns_cost_and_consumes_slot(self):
        with patch(CREATE, return_value=_completion()):
            response = self.post()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        log = APICostLog.objects.get()
        self.assertGreater(body["cost"], 0)
        self.assertEqual(body["cost"], log.estimated_cost)
        self.assertEqual(body["errors"], [])
        self.assertEqual(body["words"], [{"term": "book", "number": 2, "meaning": "本"}])
        self.assertEqual(log.user, self.user)
        self.assertEqual(OCRDailyUsage.objects.get().count, 1)

    @override_settings(OCR_DAILY_LIMIT=1, DEMO_MODE=True)
    def test_demo_limit_reached_refuses_without_calling_api(self):
        with patch(CREATE, return_value=_completion()) as create:
            self.assertEqual(self.post().status_code, 200)
            create.reset_mock()
            response = self.post()
            create.assert_not_called()
        self.assertEqual(response.status_code, 429)
        self.assertIn("本日のデモOCR利用上限（1回）に達しました", response.json()["err"])
        self.assertEqual(OCRDailyUsage.objects.get().count, 1)
        self.assertEqual(APICostLog.objects.count(), 1)

    @override_settings(OCR_DAILY_LIMIT=1, DEMO_MODE=False)
    def test_normal_limit_reached_message_has_no_demo_wording(self):
        with patch(CREATE, return_value=_completion()) as create:
            self.post()
            create.reset_mock()
            response = self.post()
            create.assert_not_called()
        self.assertEqual(response.status_code, 429)
        err = response.json()["err"]
        self.assertIn("本日のOCR利用上限（1回）に達しました", err)
        self.assertNotIn("デモ", err)

    @override_settings(OCR_DAILY_LIMIT=0, DEMO_MODE=True)
    def test_zero_limit_means_stopped(self):
        with patch(CREATE, return_value=_completion()) as create:
            response = self.post()
            create.assert_not_called()
        self.assertEqual(response.status_code, 429)
        self.assertIn("停止", response.json()["err"])
        self.assertEqual(OCRDailyUsage.objects.count(), 0)

    @override_settings(OCR_DAILY_LIMIT=3, DEMO_MODE=False)
    def test_api_failure_returns_502_and_still_consumes_slot(self):
        with patch(CREATE, side_effect=RuntimeError("boom")):
            with self.assertLogs("ocr.views", level="ERROR"):
                response = self.post()
        self.assertEqual(response.status_code, 502)
        self.assertIn("OCRに失敗しました", response.json()["err"])
        self.assertEqual(OCRDailyUsage.objects.get().count, 1)
        self.assertEqual(APICostLog.objects.count(), 0)

    @override_settings(OCR_DAILY_LIMIT=3, DEMO_MODE=False)
    def test_invalid_cost_log_does_not_fail_request(self):
        class InvalidForm(APICostLogForm):
            def is_valid(self):
                self.add_error(None, "invalid for test")
                return False

        with patch(CREATE, return_value=_completion()), patch("ocr.views.APICostLogForm", InvalidForm):
            with self.assertLogs("ocr.views", level="WARNING") as logs:
                response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["words"]), 1)
        self.assertIn("invalid for test", logs.output[0])
        self.assertEqual(APICostLog.objects.count(), 0)

    @override_settings(OCR_DAILY_LIMIT=3, DEMO_MODE=True)
    def test_missing_file_is_rejected_before_reserving(self):
        with patch(CREATE, return_value=_completion()) as create:
            response = self.post(with_file=False)
            create.assert_not_called()
        self.assertEqual(response.status_code, 400)
        self.assertIn("err", response.json())
        self.assertEqual(OCRDailyUsage.objects.count(), 0)

    @override_settings(OCR_DAILY_LIMIT=-1, DEMO_MODE=False)
    def test_unlimited_works_without_usage_rows(self):
        with patch(CREATE, return_value=_completion()):
            self.assertEqual(self.post().status_code, 200)
            self.assertEqual(self.post().status_code, 200)
        self.assertEqual(OCRDailyUsage.objects.count(), 0)
        self.assertEqual(APICostLog.objects.count(), 2)

    @override_settings(OCR_DAILY_LIMIT=3, DEMO_MODE=True)
    def test_anonymous_user_cannot_consume_quota(self):
        self.client.logout()
        with patch(CREATE, return_value=_completion()) as create:
            response = self.post()
            create.assert_not_called()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(OCRDailyUsage.objects.count(), 0)

    @override_settings(OCR_DAILY_LIMIT=3, DEMO_MODE=True, API_KEY="")
    def test_missing_api_key_does_not_consume_quota(self):
        with patch(CREATE, return_value=_completion()) as create:
            with self.assertLogs("ocr.views", level="ERROR"):
                response = self.post()
            create.assert_not_called()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(OCRDailyUsage.objects.count(), 0)

    @override_settings(OCR_DAILY_LIMIT=3, DEMO_MODE=False)
    def test_unparsable_response_still_records_cost(self):
        completion = _completion()
        completion.choices[0].message.content = "not json"
        with patch(CREATE, return_value=completion):
            with self.assertLogs("ocr.views", level="ERROR"):
                response = self.post()
        self.assertEqual(response.status_code, 502)
        self.assertGreater(APICostLog.objects.get(request_id="test-request").estimated_cost, 0)
        self.assertEqual(OCRDailyUsage.objects.get().count, 1)

    @override_settings(OCR_DAILY_LIMIT=3, DEMO_MODE=True)
    def test_database_error_while_reserving_returns_json_503(self):
        with patch(CREATE, return_value=_completion()) as create, \
                patch("ocr.views.reserve_ocr_slot", side_effect=OperationalError("database is locked")):
            with self.assertLogs("ocr.views", level="ERROR"):
                response = self.post()
            create.assert_not_called()
        self.assertEqual(response.status_code, 503)
        self.assertIn("現在OCRを利用できません", response.json()["err"])
