from django.urls import path

from .views import TestConfigureView

app_name = "quiz"

urlpatterns = [
    path("configure/", TestConfigureView.as_view(), name="configure"),
]