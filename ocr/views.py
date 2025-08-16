from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse

from .modules.gpt import GPT4oMini


class InterfaceView(TemplateView):

    def get(self, request):
        return render(request, "ocr/interface.html")


class OcrView(TemplateView):

    def post(self, request):

        files = request.FILES.getlist("files")
        gpt = GPT4oMini()
        res = gpt.request(files)
        print(res)

        return JsonResponse({"message": f"{len(files)}件アップロードしました"})