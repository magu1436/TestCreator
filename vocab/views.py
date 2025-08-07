from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class EditView(LoginRequiredMixin, TemplateView):
    login_url = "accounts:login"
    redirect_field_name = "vocab:editor"

    def get(self, request):
        return render(request, "vocab/edit.html")
    
    def post(self, request):
        return self.get(request)