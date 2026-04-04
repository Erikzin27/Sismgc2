from django.urls import path
from .views import CalendarioView, CalendarioEventosView

app_name = "calendario"

urlpatterns = [
    path("", CalendarioView.as_view(), name="index"),
    path("eventos/", CalendarioEventosView.as_view(), name="eventos"),
]
