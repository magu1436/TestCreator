from django.urls import path

from .views import TestConfigureView, CreateTestView, PreviewTestView

app_name = "quiz"

urlpatterns = [
    path("configure/", TestConfigureView.as_view(), name="configure"),
    path("create/", CreateTestView.as_view(), name="create"),
    path("preview/", PreviewTestView.as_view(), name="preview"),
]