from django.urls import path

from .views import EditView

app_name = "vocab"

urlpatterns = [
    path("editor/", EditView.as_view(), name="editor"),
]