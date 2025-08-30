import random
import json

from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.db.models import Q

from wordbank.models import WordList
from vocab.models import Word
from .modules.creator import create_pdf


class TestConfigureView(TemplateView):
    def get(self, request):
        default_wordlist = WordList.objects.first()
        return render(request, "quiz/configure.html", {"wordlist": default_wordlist})


class CreateTestView(TemplateView):

    def post(self, request):

        configure = json.loads(request.body)
        print(configure)
        wordlist_id = configure["wordlistId"]
        wordlist = get_object_or_404(WordList, pk=wordlist_id)
        ranges = configure["ranges"]
        num_question = configure["numQuestion"]
        sequence = ""
        match configure["sequence"]:
            case "random": sequence = "ランダム"
            case "sequence": sequence = "昇順"
            case _: raise ValueError(f"sequence value error: {sequence}")

        q_obj = Q()
        for range in ranges:
            q_obj.add(Q(number__range=(range["start"], range["end"])), Q.OR)
        words = list(Word.objects.filter(Q(wordlist=wordlist), q_obj).order_by("number"))
        if sequence == "ランダム":
            words = random.sample(words, k=(min(num_question, len(words))))
        print(words)
        
        param = {
            "wordlist": wordlist,
            "ranges": ranges,
            "num_question": num_question,
            "sequence": sequence,
            "words": words,
            "mode": "problem",
        }

        html = render_to_string("quiz/quiz.html", param, request)
        print(html)
        create_pdf(html)

        return JsonResponse({"ok": True})