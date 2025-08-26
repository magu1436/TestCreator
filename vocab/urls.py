from django.urls import path

from .views import EditView, RegisterView, DeleteView, UpdateView

app_name = "vocab"

urlpatterns = [
    path("editor/", EditView.as_view(), name="editor"),
    path("editor/register/", RegisterView.as_view(), name="register"),
    path("editor/delete/", DeleteView.as_view(), name="delete"),
    path("editor/update/", UpdateView.as_view(), name="update"),
]