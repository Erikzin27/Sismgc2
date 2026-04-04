from django.urls import path
from . import views

app_name = "historico"

urlpatterns = [
    path("", views.HistoricoListView.as_view(), name="list"),
]
