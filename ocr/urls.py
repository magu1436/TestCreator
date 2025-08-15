from django.urls import path

from .views import InterfaceView

app_name = "ocr"

urlpatterns = [
    path("", InterfaceView.as_view(), name="interface"),
]