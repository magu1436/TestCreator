import json

from django.views.generic import TemplateView
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from django.db.models import F
from django.db.models.deletion import ProtectedError

from .models import WordList
from .forms import WordlistForm
from vocab.models import Word


class CreateView(TemplateView):
    def post(self, request):
        form = WordlistForm(data=request.POST.copy())
        if form.is_valid():
            wordlist = form.save(commit=False)
            wordlist.created_by = self.request.user
            wordlist.save()
            return JsonResponse(
                {"ok": True, "id": wordlist.id, "name": wordlist.name},
                status=201)
        else:
            return JsonResponse(
                {"ok": False, "error": form.errors}, 
                status=400
                )


class DeleteView(TemplateView):
    def post(self, request):
        id = int(json.loads(request.body)["id"])
        wordlist = get_object_or_404(WordList, pk=id)
        wordlist_name = wordlist.name

        words_on_wordlists = Word.objects.filter(wordlist=wordlist)
        
        try:
            for word in words_on_wordlists:
                word.delete()
            wordlist.delete()
        except ProtectedError:
            return JsonResponse(
                {"ok": False, "error": "他のデータが参照しているため, 一部または全てのレコードを削除できません."},
                status=409
            )

        return JsonResponse({"ok": True, "name": wordlist_name}, status=200)


class ReadView(TemplateView):
    def post(self, request):
        try:
            id = int(json.loads(request.body)["id"])
            wordlist = get_object_or_404(WordList, pk=id)
            words = list(
                Word.objects.filter(wordlist=wordlist)
                            .select_related("latest_edited_by")
                            .values("id", "number", "term", "meaning", editor=F("latest_edited_by__username"))
                            .order_by("number")
                        )
            return JsonResponse({
                "ok": True,
                "name": wordlist.name,
                "words": words,
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "ok": False,
                "err": e,
            })


class GetAllWordlistView(TemplateView):
    def get(self, request):
        wordlists = list(WordList.objects.values("id", "name").order_by("id"))
        return JsonResponse({
            "wordlists": wordlists,
        }, status=200)