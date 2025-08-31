import json
from pathlib import Path

from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse, FileResponse
from django.views.generic import TemplateView
from django.urls import reverse
from django.utils.encoding import iri_to_uri
from django.conf import settings

from wordbank.models import WordList
from .modules.creator import create_pdf
from .modules.configure import create_configure


class TestConfigureView(TemplateView):
    def get(self, request):
        default_wordlist = WordList.objects.first()
        return render(request, "quiz/configure.html", {"wordlist": default_wordlist})


class CreateTestView(TemplateView):

    def post(self, request):

        configure = json.loads(request.body)
        context = create_configure(configure)

        html = render_to_string("quiz/quiz.html", context, request)
        file_name = create_pdf(html)

        file_path = Path(settings.OUTPUT_PDF_DIR, file_name)
        f = open(file_path, "rb")
        response = FileResponse(f, content_type="application/pdf")
        response["Content-Disposition"] = f"inline; filename*=UTF-8''{iri_to_uri(file_name)}"

        return response


class PreviewTestView(TemplateView):

    def get(self, request):
        config = request.session.get("preview_config")
        if not config:
            raise ValueError("config is not set.")
        return render(request, "quiz/quiz.html", config)

    def post(self, request):
        configure = json.loads(request.body)
        request.session["preview_config"] = create_configure(configure)
        return JsonResponse({"redirect_url": reverse("quiz:preview")})