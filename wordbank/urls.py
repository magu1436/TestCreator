from django.urls import path

from .views import CreateView, DeleteView, ReadView, GetAllWordlistView

app_name = "wordbank"

urlpatterns = [
    path("create/", CreateView.as_view(), name="create"),
    path("delete/", DeleteView.as_view(), name="delete"),
    path("read/", ReadView.as_view(), name="read"),
    path("get_all_wordlist/", GetAllWordlistView.as_view(), name="all_wordlist"),
]