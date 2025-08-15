from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse

from .models import UploadedFile


class InterfaceView(TemplateView):

    def get(self, request):
        return render(request, "ocr/interface.html")


class OcrView(TemplateView):

    def post(self, request):
        files = request.FILES.getlist("files")
        for f in files:
            UploadedFile.objects.create(file=f)
        return JsonResponse({"message": f"{len(files)}件アップロードしました"})