"""OCRの1日あたり利用回数の上限管理。

利用枠は外部API呼び出しの開始時点で消費する。上限は全利用者の合計で、
日付の境界は settings.TIME_ZONE のローカル日付とする。
複数プロセス・スレッドからの同時実行でも上限を超えないよう、
DB上の条件付きUPDATE(count < limit)で原子的に予約する。
"""
import logging
from dataclasses import dataclass

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from .models import OCRDailyUsage

logger = logging.getLogger(__name__)

# OCR_DAILY_LIMIT未設定かつデモ環境のときの既定上限。
DEFAULT_DEMO_DAILY_LIMIT = 10


@dataclass(frozen=True)
class ReservationResult:
    """利用枠の予約結果。limitがNoneのときは無制限。usedは予約後(拒否時は現在)の利用回数。"""
    allowed: bool
    limit: int | None
    used: int | None


def get_daily_limit():
    """実効的な1日あたりの上限を返す。Noneは無制限、0はOCR停止。"""
    configured = settings.OCR_DAILY_LIMIT
    if configured is None:
        return DEFAULT_DEMO_DAILY_LIMIT if settings.DEMO_MODE else None
    if configured == -1:
        return None
    return configured


def _increment_if_below(date, limit):
    """上限未満のときだけ利用回数を1増やす。更新した行数(0または1)を返す。"""
    return OCRDailyUsage.objects.filter(date=date, count__lt=limit).update(count=F("count") + 1)


def reserve_ocr_slot():
    """今日の利用枠を1回分予約する。外部API呼び出しの直前に呼ぶこと。"""
    limit = get_daily_limit()
    if limit is None:
        return ReservationResult(allowed=True, limit=None, used=None)

    today = timezone.localdate()
    if limit == 0:
        logger.warning("OCR利用を拒否しました(OCR停止中): date=%s used=0 limit=0", today)
        return ReservationResult(allowed=False, limit=0, used=0)

    # 読み取り後に書き込むトランザクションはSQLiteでロック昇格に失敗するため使わず、
    # 1文で完結する書き込み(条件付きUPDATE・INSERT)だけで予約する。
    updated = _increment_if_below(today, limit)
    if not updated:
        try:
            with transaction.atomic():
                OCRDailyUsage.objects.create(date=today, count=1)
            updated = 1
        except IntegrityError:
            # 当日の行が既にある(または同時に作成された)ので、条件付きUPDATEをやり直す。
            updated = _increment_if_below(today, limit)
    # usedはログと表示用の参考値(同時実行時は直後の値と異なる場合がある)。
    used = OCRDailyUsage.objects.values_list("count", flat=True).get(date=today)

    if updated == 1:
        logger.info("OCR利用枠を予約しました: date=%s used=%s limit=%s", today, used, limit)
        return ReservationResult(allowed=True, limit=limit, used=used)

    logger.warning("OCR利用を拒否しました(上限到達): date=%s used=%s limit=%s", today, used, limit)
    return ReservationResult(allowed=False, limit=limit, used=used)
