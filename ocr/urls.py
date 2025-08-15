from django.urls import path

from .views import InterfaceView, OcrView

app_name = "ocr"

urlpatterns = [
    path("", InterfaceView.as_view(), name="interface"),
    path("ocr", OcrView.as_view(), name="ocr"),
]