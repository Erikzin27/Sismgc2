from django.urls import path
from . import views

app_name = "estoque"

urlpatterns = [
    path("", views.ItemListView.as_view(), name="list"),
    path("novo/", views.ItemCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ItemDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.ItemUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", views.ItemDeleteView.as_view(), name="delete"),
    path("movimentos/", views.MovimentoListView.as_view(), name="mov_list"),
    path("movimentos/novo/", views.MovimentoCreateView.as_view(), name="mov_create"),
]
