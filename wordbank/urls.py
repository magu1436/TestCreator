from django.urls import path

from .views import CreateView, DeleteView

app_name = "wordbank"

urlpatterns = [
    path("create/", CreateView.as_view(), name="create"),
    path("delete/", DeleteView.as_view(), name="delete"),
]