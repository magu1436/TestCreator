import json
from pathlib import Path
import io
from typing import Final

import pypdf

from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse, FileResponse
from django.views.generic import TemplateView
from django.urls import reverse
from django.utils.encoding import iri_to_uri
from django.utils import timezone
from django.conf import settings

from wordbank.models import WordList
from .modules.creator import create_pdf
from .modules.configure import create_configure


FILE_NAME_FORMAT: Final[str] = "%Y_%m_%d_%H_%M_%S_%f.pdf"


class TestConfigureView(TemplateView):
    def get(self, request):
        default_wordlist = WordList.objects.first()
        return render(request, "quiz/configure.html", {"wordlist": default_wordlist})


class CreateTestView(TemplateView):

    def post(self, request):

        configure = json.loads(request.body)
        context = create_configure(configure)

        pdfs = []
        for mode in ("question", "answer"):
            context["mode"] = mode
            html = render_to_string("quiz/quiz.html", context, request)
            pdfs.append(io.BytesIO(create_pdf(html)))
        
        writer = pypdf.PdfWriter()
        [writer.append(pdf) for pdf in pdfs]
        file_name = create_name()
        writer.write(Path(settings.OUTPUT_PDF_DIR, file_name))

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
    

def create_name():
    now = timezone.localtime(timezone.now())
    return now.strftime(FILE_NAME_FORMAT)