from django.shortcuts import render
from django.views.generic import TemplateView


class InterfaceView(TemplateView):

    def get(self, request):
        return render(request, "ocr/interface.html")