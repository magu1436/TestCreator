from django import forms

from .models import APICostLog


class APICostLogForm(forms.ModelForm):
    class Meta:
        model = APICostLog
        fields = ["user", "estimated_cost", "request_id", "api_model"]