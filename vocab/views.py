import json

from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder

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
            "words": [model_to_dict(word, ["id", "term", "meaning", "latest_edited_by"]) for word in params["words"]],
            "target_wordlist": model_to_dict(params["target_word_list"], ["id", "name"]),
            "wordlists": [model_to_dict(wordlist, ["id", "name"]) for wordlist in params["word_lists"]],
        }
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
            return JsonResponse({"ok": True, "id": word.id, "editor": self.request.user.username}, status=201)
        else:
            return JsonResponse({"ok": False, "error": form.errors}, status=400)