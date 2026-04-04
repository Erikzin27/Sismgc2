from django.urls import path
from . import views

app_name = "lotes"

urlpatterns = [
    path("", views.LoteListView.as_view(), name="list"),
    path("novo/", views.LoteCreateView.as_view(), name="create"),
    path("<int:pk>/", views.LoteDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.LoteUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", views.LoteDeleteView.as_view(), name="delete"),
]
