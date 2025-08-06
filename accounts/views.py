
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import LogoutView as BaseLogoutView
from django.urls import reverse_lazy

from .forms import LoginForm


class LoginView(BaseLoginView):
    form_class = LoginForm
    template_name = "accounts/login.html"


class LogoutView(BaseLogoutView):
    next_page = "home"