from django.shortcuts import render
from django.views.generic import TemplateView

from wordbank.models import WordList


class TestConfigureView(TemplateView):
    def get(self, request):
        default_wordlist = WordList.objects.first()
        return render(request, "quiz/configure.html", {"wordlist": default_wordlist})
    