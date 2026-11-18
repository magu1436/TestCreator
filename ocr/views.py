import logging

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.conf import settings

from .modules.gpt import GPT4oMini
from .forms import APICostLogForm
from .quota import reserve_ocr_slot
from wordbank.models import WordList

logger = logging.getLogger(__name__)


class InterfaceView(TemplateView):

    def get(self, request):
        target_wordlist_id = self.request.GET.get("wordlist")
        target_wordlist = get_object_or_404(WordList, pk=target_wordlist_id)
        return render(request, "ocr/interface.html", {"target_word_list": target_wordlist})


def _build_refusal_message(limit: int) -> str:
    """利用枠を確保できなかったときの利用者向けメッセージを作る。"""
    prefix = "デモ" if settings.DEMO_MODE else ""
    if limit == 0:
        return f"現在{prefix}OCRは停止しています。単語の手動編集やテスト作成は引き続き利用できます。"
    return (
        f"本日の{prefix}OCR利用上限（{limit}回）に達しました。"
        "時間をおいてお試しください。単語の手動編集やテスト作成は引き続き利用できます。"
    )


class OcrView(TemplateView):

    def post(self, request):

        # 入力検証は利用枠を消費する前に行う。
        files = request.FILES.getlist("files")
        if not files:
            return JsonResponse({"err": "OCRする画像ファイルが選択されていません。"}, status=400)

        reservation = reserve_ocr_slot()
        if not reservation.allowed:
            return JsonResponse({"err": _build_refusal_message(reservation.limit)}, status=429)

        # 利用枠はAPI呼び出しの成否にかかわらず消費済みとして扱う。
        gpt = GPT4oMini()
        res = gpt.request(files[0])

        if res["errors"] or res["words"] is None:
            for error in res["errors"]:
                logger.error("OCRのAPI呼び出しに失敗しました", exc_info=error)
            if not res["errors"]:
                logger.error("OCRのAPI呼び出しに失敗しました(結果が空です)")
            return JsonResponse(
                {"err": "OCRに失敗しました。時間をおいて再度お試しください。"},
                status=502,
            )

        form = APICostLogForm(data={
            "user": request.user.pk,
            "estimated_cost": res["estimated_cost"],
            "request_id": res["request_id"],
            "api_model": res["api_model"],
        })
        if form.is_valid():
            form.save()
        else:
            # 費用記録の失敗で、成功したOCR結果を利用者に返せなくならないようにする。
            logger.warning("APICostLogを保存できませんでした: %s", form.errors.as_json())

        return JsonResponse({
            "message": f"{len(files)}件アップロードしました",
            "words": res["words"],
            "cost": res["estimated_cost"],
            "errors": [],
        })
