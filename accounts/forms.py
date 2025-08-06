
from django.contrib.auth.forms import AuthenticationForm

from .models import AdminUser


class LoginForm(AuthenticationForm):
    class Meta:
        model = AdminUser