import json

from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.deletion import ProtectedError

from .models import Word
from .forms import WordForm
from wordbank.models import WordList


class EditView(LoginRequiredMixin, TemplateView):
    login_url = "accounts:login"
    redirect_field_name = "vocab:editor"

    def get(self, request):
        params = {}
        word_lists = WordList.objects
        if not self.request.GET:
            target_word_list = word_lists.first()
        else:
            target_word_list_name = self.request.GET.get("target_word_list")
            target_word_list = WordList.objects.filter(name=target_word_list_name).first()
        words = Word.objects.filter(wordlist=target_word_list.id)
        params["words"] = words
        params["target_word_list"] = target_word_list
        params["word_lists"] = word_lists.exclude(id=target_word_list.id)

        json_data = {
            "words": [model_to_dict(word, ["id", "number", "term", "meaning"]) for word in params["words"]],
            "target_wordlist": model_to_dict(params["target_word_list"], ["id", "name"]),
            "wordlists": [model_to_dict(wordlist, ["id", "name"]) for wordlist in params["word_lists"]],
        }
        for word_dict, word in zip(json_data["words"], params["words"]):
            word_dict["latest_edited_by"] = word.latest_edited_by.username
        params["json_data"] = json.dumps(json_data, ensure_ascii=False, cls=DjangoJSONEncoder)
        return render(request, "vocab/edit.html", params)
    
    def post(self, request):
        return self.get(request)


class RegisterView(TemplateView):
    def post(self, request):
        data: dict = request.POST.copy()

        form = WordForm(data=data)
        if form.is_valid():
            word = form.save(commit=False)
            word.latest_edited_by = self.request.user
            word.save()
            return JsonResponse({
                "ok": True, 
                "id": word.id, 
                "number": word.number,
                "term": word.term,
                "meaning": word.meaning,
                "editor": self.request.user.username
                }, status=201)
        else:
            return JsonResponse({"ok": False, "error": form.errors}, status=400)


class DeleteView(TemplateView):
    def post(self, request):
        ids = json.loads(request.body)["ids"]
        words = [get_object_or_404(Word, pk=id) for id in ids]

        try:
            for word in words:
                word.delete()
        except ProtectedError:
            return JsonResponse(
                {"ok": False, "error": "他のデータが参照しているため一部または全ての単語を削除できません."},
                status=409
            )
        
        return JsonResponse({"ok": True}, status=200)


