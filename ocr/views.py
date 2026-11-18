import logging

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.conf import settings
from django.db import DatabaseError

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

        # 有料APIのため、未ログインの利用者には共有の利用枠を使わせない(全環境で拒否)。
        # Ajaxの呼び出し元がエラー内容を受け取れるよう、LoginRequiredMixinのリダイレクトではなくJSONの403を返す。
        if not request.user.is_authenticated:
            return JsonResponse({"err": "OCRを利用するにはログインしてください。"}, status=403)

        # 入力検証と設定確認は利用枠を消費する前に行う。
        files = request.FILES.getlist("files")
        if not files:
            return JsonResponse({"err": "OCRする画像ファイルが選択されていません。"}, status=400)
        if not settings.API_KEY:
            logger.error("OpenAI APIキーが設定されていないため、OCRを実行できません")
            return JsonResponse({"err": "現在OCRを利用できません。"}, status=503)

        try:
            reservation = reserve_ocr_slot()
        except DatabaseError:
            # SQLiteの書き込み待ちのタイムアウトなど。枠は消費されていないため、利用者には一時的な停止として返す。
            logger.exception("OCR利用枠を確保できませんでした")
            return JsonResponse({"err": "現在OCRを利用できません。時間をおいて再度お試しください。"}, status=503)
        if not reservation.allowed:
            return JsonResponse({"err": _build_refusal_message(reservation.limit)}, status=429)

        # 利用枠はAPI呼び出しの成否にかかわらず消費済みとして扱う。
        gpt = GPT4oMini()
        res = gpt.request(files[0])

        # 課金された呼び出し(費用を算出できたもの)は、応答の解析に失敗しても費用を記録する。
        if res["estimated_cost"] is not None:
            self._save_cost_log(request, res)

        if res["errors"]:
            for error in res["errors"]:
                logger.error("OCRのAPI呼び出しに失敗しました", exc_info=error)
            return JsonResponse(
                {"err": "OCRに失敗しました。時間をおいて再度お試しください。"},
                status=502,
            )

        return JsonResponse({
            "message": f"{len(files)}件アップロードしました",
            "words": res["words"],
            "cost": res["estimated_cost"],
            "errors": [],
        })

    @staticmethod
    def _save_cost_log(request, res):
        form = APICostLogForm(data={
            "user": request.user.pk,
            "estimated_cost": res["estimated_cost"],
            "request_id": res["request_id"],
            "api_model": res["api_model"],
        })
        if form.is_valid():
            form.save()
        else:
            # 費用記録の失敗で、OCRの結果を利用者に返せなくならないようにする。
            logger.warning("APICostLogを保存できませんでした: %s", form.errors.as_json())
