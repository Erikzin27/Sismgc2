from django.urls import path
from . import views

app_name = "nascimentos"

urlpatterns = [
    path("", views.NascimentoListView.as_view(), name="list"),
    path("novo/", views.NascimentoCreateView.as_view(), name="create"),
    path("<int:pk>/", views.NascimentoDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.NascimentoUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", views.NascimentoDeleteView.as_view(), name="delete"),
]
