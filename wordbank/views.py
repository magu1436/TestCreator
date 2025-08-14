from django.views.generic import TemplateView
from django.http import JsonResponse

from .forms import WordlistForm


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