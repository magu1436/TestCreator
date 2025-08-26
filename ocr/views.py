from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.http import JsonResponse

from .modules.gpt import GPT4oMini
from wordbank.models import WordList


class InterfaceView(TemplateView):

    def get(self, request):
        target_wordlist_id = self.request.GET.get("wordlist")
        target_wordlist = get_object_or_404(WordList, pk=target_wordlist_id)
        return render(request, "ocr/interface.html", {"target_word_list": target_wordlist})


class OcrView(TemplateView):

    def post(self, request):

        files = request.FILES.getlist("files")
        gpt = GPT4oMini()
        res = gpt.request(files)
        print(res)

        return JsonResponse({"message": f"{len(files)}件アップロードしました"})