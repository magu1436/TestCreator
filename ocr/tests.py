import datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings

from TestCreator.settings import parse_ocr_daily_limit

from .models import OCRDailyUsage
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
