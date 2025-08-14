from django import forms

from .models import WordList


class WordlistForm(forms.ModelForm):
    class Meta:
        model = WordList
        fields = ["name"]